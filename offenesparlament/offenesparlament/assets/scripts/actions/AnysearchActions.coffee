AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
AnysearchConstants = require('../constants/AnysearchConstants.coffee')


AnysearchActions =
  createTerm: (category, value) ->
    AppDispatcher.dispatch({
      actionType: AnysearchConstants.CREATE_TERM
      category: category
      value: value
    })

  createPermanentTerm: (category, value) ->
    AppDispatcher.dispatch({
      actionType: AnysearchConstants.CREATE_PERMANENT_TERM
      category: category
      value: value
    })

  deleteTerm: (id) ->
    AppDispatcher.dispatch({
      actionType: AnysearchConstants.DELETE_TERM
      id: id
    })

  changeTermValue: (id, value) ->
    AppDispatcher.dispatch({
      actionType: AnysearchConstants.CHANGE_TERM_VALUE
      id: id
      value: value
    })

  changeTermCategory: (id, category) ->
    AppDispatcher.dispatch({
      actionType: AnysearchConstants.CHANGE_TERM_CATEGORY
      id: id
      category: category
    })

  updateFacets: (selected_term_id) ->
    AppDispatcher.dispatch({
      actionType: AnysearchConstants.UPDATE_FACETS
      selected_term_id: selected_term_id
    })


module.exports = AnysearchActions
