AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
EventEmitter = require('events').EventEmitter
AnysearchConstants = require('../constants/AnysearchConstants.coffee')
RouterActions = require('../actions/RouterActions.coffee')
assign = require('object-assign')
$ = require 'jquery'
_ = require 'underscore'
string_utils = require '../utils/StringUtils.coffee'


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


_process_edit = () ->
  if _setup_complete then _was_edited_by_user = true

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
    if not _was_edited_by_user and term.category == 'llps'
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
    _debounced_update_search_results()
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

_get_url = () ->
  type_term = _get_term_by_category('type')
  if type_term?
    switch type_term.value
      when 'Personen'
        return '/personen/search'
      when 'Gesetze'
        return '/gesetze/search'
  return '/search'

_update_search_results = () ->
  _loading = true
  $.ajax
    url: _get_url()
    dataType: 'json'
    data: _get_terms_as_object()
    success: (response) ->
      if response.result?
        _search_results = response.result
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
      url: _get_url()
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
            _suggested_values = ['Personen', 'Gesetze']
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

  get_subscription_url: () ->
    return _get_url() + '?' + $.param(_get_terms_as_object())

  get_subscription_title: () ->
    return string_utils.get_search_title(_get_terms_as_object())

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
      when AnysearchConstants.SEARCHBAR_SETUP_COMPLETE
        _setup_complete = true
    return true # No errors. Needed by promise in Dispatcher.
  )
})


_pad_terms_with_helpers()  # We want to have at least one helper-term when term-array is empty in the beginning

module.exports = AnysearchStore
