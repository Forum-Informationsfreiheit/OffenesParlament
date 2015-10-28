AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
EventEmitter = require('events').EventEmitter
AnysearchConstants = require('../constants/AnysearchConstants.coffee')
assign = require('object-assign')
_ = require 'underscore'


CHANGE_EVENT = 'change'
SERVER_DEBOUNCE_INTERVAL = 200

_id_counter = 0
_terms = []
_loading = false
_suggested_categories = []
_suggested_values = []
_search_results = null

_create_term = (category, value, helper=false) ->
  new_term =
    id: _id_counter
    category: category
    value: value
    helper: helper
  _id_counter += 1
  return new_term

_add_term = (category, value) ->
  _terms.push(_create_term(category, value))
  _pad_terms_with_helpers()

_pad_terms_with_helpers = () ->
  terms = _.filter(_terms, (term) -> return (not term.helper))
  if terms.length > 0 then terms.unshift(_create_term('', '', true))
  terms.push(_create_term('', '', true))
  _terms = terms

_change_term_value = (id, value) ->
  term = _.find(_terms, (term) -> return term.id == id)
  if term?
    if term.helper
      term.helper = false
      term.category = 'q'
    term.value = value
    _pad_terms_with_helpers()
    _debounced_update_search_results()

_change_term_category = (id, category) ->
  term = _.find(_terms, (term) -> return term.id == id)
  if term?
    if term.helper
      term.helper = false
    term.category = category
    _pad_terms_with_helpers()
    _update_facets(id)
    _debounced_update_search_results()

_get_terms_as_object = (excluded_term) ->
  return _.object(_.compact(_.map(_terms, (term) ->
    if term.helper or (excluded_term and excluded_term.category == term.category)
      return null
    else
      return [term.category, term.value]
  )))

_update_search_results = () ->
  _loading = true
  $.ajax
    url: '/personen/search'
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
  term = _.find(_terms, (term) -> return term.id == selected_term_id)
  if term?
    $.ajax
      url: '/personen/search'
      dataType: 'json'
      data: _.extend({only_facets: 1}, _get_terms_as_object(term))
      success: (response) ->
        if response.facets?.fields?
          _suggested_categories = _.keys(response.facets.fields)
          if not _.has(_suggested_categories, 'q') then _suggested_categories.push('q')
          if _.has(response.facets.fields, term.category)
            _suggested_values = _.map(response.facets.fields[term.category], (item) -> return item[0])
          else
            _suggested_values = []
      complete: () ->
        _loading = false
        AnysearchStore.emitChange()


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
      when AnysearchConstants.CHANGE_TERM_VALUE
        _change_term_value(payload.id, payload.value)
        AnysearchStore.emitChange()
      when AnysearchConstants.CHANGE_TERM_CATEGORY
        _change_term_category(payload.id, payload.category)
        AnysearchStore.emitChange()
      when AnysearchConstants.UPDATE_FACETS
        _update_facets(payload.selected_term_id)
        AnysearchStore.emitChange()
    return true # No errors. Needed by promise in Dispatcher.
  )
})


_pad_terms_with_helpers()  # We want to have at least one helper-term when term-array is empty in the beginning

module.exports = AnysearchStore
