AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
EventEmitter = require('events').EventEmitter
AnysearchConstants = require('../constants/AnysearchConstants.coffee')
RouterActions = require('../actions/RouterActions.coffee')
assign = require('object-assign')
$ = require 'jquery'
_ = require 'underscore'
string_utils = require '../utils/StringUtils.coffee'
deparam = require('jquery-deparam')


CHANGE_EVENT = 'change'
SERVER_DEBOUNCE_INTERVAL = 200
LLP_REGEXP = /(.+)(\()([XVICDM]{1,})(\))/  # matches "aktuell seit 2013-10-29 (XXV)" and used to extract "XXV"

_id_counter = 0
_terms = []
_loading = false
_suggested_categories = []
_suggested_values = []
_search_results = null
_setup_complete = false
_was_edited_by_user = false
_current_search_url = ''
_routing_active = false
_subscription_allowed = false
_projected_result_count = null
_pagination_offset = 0


_process_edit = () ->
  if _setup_complete
    _was_edited_by_user = true
    _pagination_offset = 0

_get_term = (id) ->
  return _.find(_terms, (term) -> return term.id == id)

_get_term_by_category = (category) ->
  return _.find(_terms, (term) -> return term.category == category)

_create_term = (category, value, helper=false, permanent=false) ->
  new_term =
    id: _id_counter
    category: category
    value: value
    helper: helper
    permanent: permanent
  _id_counter += 1
  return new_term

_delete_term = (id) ->
  _terms = _.filter(_terms, (term) -> return term.id != id)
  _pad_terms_with_helpers()
  _debounced_update_search_results()
  _process_edit()

_add_term = (category, value, helper=false, permanent=false) ->
  _terms.push(_create_term(category, value, helper, permanent))
  _pad_terms_with_helpers()
  _process_edit()

_pad_terms_with_helpers = () ->
  terms = _.filter(_terms, (term) -> return (not term.helper))
  # if terms.length > 0 then terms.unshift(_create_term('', '', true))
  terms.push(_create_term('', '', true))
  _terms = terms

_change_term_value = (id, value) ->
  term = _get_term(id)
  if term?
    if term.helper
      term.helper = false
      term.category = 'q'
    term.value = value
    if not _was_edited_by_user and term.category == 'llps' and _routing_active
      RouterActions.changeLlpUrl(_parse_term_value(value, term.category))
    else
      _pad_terms_with_helpers()
      _debounced_update_search_results()
      _process_edit()

_change_term_category = (id, category) ->
  term = _get_term(id)
  if term?
    if term.helper
      term.helper = false
    term.category = category
    _pad_terms_with_helpers()
    _update_facets(id)
    _process_edit()

_parse_term_value = (value, category) ->
  if category == 'llps'
    matches = LLP_REGEXP.exec(value)
    if matches and matches.length == 5
      return matches[3]
    else
      return value
  else
    return value

_get_terms_as_object = (excluded_term) ->
  return _.object(_.compact(_.map(_terms, (term) ->
    if term.helper or (excluded_term and excluded_term.category == term.category)
      return null
    else
      return [term.category, _parse_term_value(term.value, term.category)]
  )))

_get_search_api_endpoint = () ->
  type_term = _get_term_by_category('type')
  if type_term?
    switch type_term.value
      when 'Personen'
        return '/personen/search'
      when 'Gesetze'
        return '/gesetze/search'
      when 'Debatten'
        return '/debatten/search'
  return '/search'

_get_search_humanfacing_endpoint = () ->
  type_term = _get_term_by_category('type')
  if type_term?
    switch type_term.value
      when 'Personen'
        return '/suche/personen'
      when 'Gesetze'
        return '/suche/gesetze'
      when 'Debatten'
        return '/suche/debatten'
  return '/suche'

_update_search_results = () ->
  _loading = true
  $.ajax
    url: _get_search_api_endpoint()
    dataType: 'json'
    data: _.extend({offset: _pagination_offset}, _get_terms_as_object())
    success: (response) ->
      if response.result?
        _search_results = response.result
        _projected_result_count = response.stats.num_results
    complete: () ->
      _loading = false
      AnysearchStore.emitChange()

_debounced_update_search_results = _.debounce(_update_search_results, SERVER_DEBOUNCE_INTERVAL)

_update_facets = (selected_term_id) ->
  _loading = true
  _suggested_categories = []
  _suggested_values = []
  term = _get_term(selected_term_id)
  if term?
    $.ajax
      url: _get_search_api_endpoint()
      dataType: 'json'
      data: _.extend({only_facets: 1}, _get_terms_as_object(term))
      success: (response) ->
        if response.facets?.fields?
          _update_suggested_categories(response.facets.fields, selected_term_id)
          if _.has(response.facets.fields, term.category)
            _suggested_values = _.compact(_.map(response.facets.fields[term.category], (item) ->
              if item[0] then return item[0]
              else return null
            ))
          else if term.category == 'type'
            _suggested_values = ['Personen', 'Gesetze', 'Debatten']
          else
            _suggested_values = []
      complete: () ->
        _loading = false
        AnysearchStore.emitChange()

_update_suggested_categories = (fields, selected_term_id) ->
  selected_term = _get_term(selected_term_id)
  if selected_term?
    categories = _.keys(fields)
    if not _.has(categories, 'q') then categories.push('q')
    if not _.has(categories, 'type') then categories.push('type')
    used_categories = _.map(_terms, (term) -> return term.category)
    _suggested_categories = _.filter(categories, (cat) ->
      return ( (not _.contains(used_categories, cat)) or cat == selected_term.category )
    )

_replace_search = (type, query) ->
  _terms = []
  query_obj = {}
  if _.isString(query)
    query_obj = deparam(query)
  if _.has(query_obj, 'llps')
    _add_term('llps', query_obj['llps'], false, true)
    query_obj = _.omit(query_obj, 'llps')
  if _.isString(type)
    _add_term('type', string_utils.capitalize_first_letter(type))
  _.each(query_obj, (value, key) ->
    _add_term(key, value)
  )
  _pad_terms_with_helpers()
  _debounced_update_search_results()


AnysearchStore = assign({}, EventEmitter.prototype, {

  get_terms: () ->
    return _terms

  is_loading: () ->
    return _loading

  get_categories: () ->
    return _suggested_categories

  get_values: () ->
    return _suggested_values

  get_search_results: () ->
    return _search_results

  get_search_ui_url: () ->
    params = _.omit(_get_terms_as_object(), (value) -> _.isEmpty(value))
    params = _.omit(params, 'type')
    return _get_search_humanfacing_endpoint() + '?' + $.param(params)

  get_subscription_url: () ->
    return _get_search_api_endpoint() + '?' + $.param(_get_terms_as_object())

  get_subscription_title: () ->
    return string_utils.get_search_title(_get_terms_as_object())

  is_subscription_allowed: () ->
    categories = _get_terms_as_object()
    if categories.llps? and
      categories.llps and
      _.compact(_.values(_.omit(categories, ['llps', 'type']))).length > 0
        return true
    else
      return false

  get_result_count: () ->
    return _projected_result_count

  get_pagination_offset: () ->
    return _pagination_offset

  emitChange: () ->
    this.emit(CHANGE_EVENT)

  addChangeListener: (callback) ->
    this.on(CHANGE_EVENT, callback)

  removeChangeListener: (callback) ->
    this.removeListener(CHANGE_EVENT, callback)

  dispatcherIndex: AppDispatcher.register( (payload) =>
    switch payload.actionType
      when AnysearchConstants.CREATE_TERM
        _add_term(payload.category, payload.value)
        AnysearchStore.emitChange()
      when AnysearchConstants.CREATE_PERMANENT_TERM
        _add_term(payload.category, payload.value, false, true)
        AnysearchStore.emitChange()
      when AnysearchConstants.DELETE_TERM
        _delete_term(payload.id)
        AnysearchStore.emitChange()
      when AnysearchConstants.CHANGE_TERM_VALUE
        _change_term_value(payload.id, payload.value)
        AnysearchStore.emitChange()
      when AnysearchConstants.CHANGE_TERM_CATEGORY
        _change_term_category(payload.id, payload.category)
        AnysearchStore.emitChange()
      when AnysearchConstants.UPDATE_FACETS
        _update_facets(payload.selected_term_id)
        AnysearchStore.emitChange()
      when AnysearchConstants.OVERRIDE_SEARCH
        _replace_search(payload.type, payload.query)
        AnysearchStore.emitChange()
      when AnysearchConstants.SEARCHBAR_SETUP_COMPLETE
        _current_search_url = AnysearchStore.get_search_ui_url()
        _setup_complete = true
      when AnysearchConstants.SEARCHBAR_ACTIVATE_ROUTING
        _current_search_url = AnysearchStore.get_search_ui_url()
        _routing_active = true
      when AnysearchConstants.SEARCHBAR_FORCE_LOCATION_CHANGE
        if not _routing_active
          _current_search_url = AnysearchStore.get_search_ui_url()
          RouterActions.changeLocation(_current_search_url)
      when AnysearchConstants.UPDATE_PAGINATION_OFFSET
        _pagination_offset = payload.offset
        _debounced_update_search_results()
        AnysearchStore.emitChange()
    new_search_url = AnysearchStore.get_search_ui_url()
    if _setup_complete and _current_search_url != new_search_url and _routing_active
      RouterActions.changeRoute(new_search_url)
      _subscription_allowed = true
      _current_search_url = new_search_url
      AnysearchStore.emitChange()
    return true # No errors. Needed by promise in Dispatcher.
  )
})


_pad_terms_with_helpers()  # We want to have at least one helper-term when term-array is empty in the beginning

module.exports = AnysearchStore
