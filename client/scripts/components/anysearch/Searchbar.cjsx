React = require 'react'
AutosizeInput = require 'react-input-autosize'
Term = require './Term.cjsx'
Suggest = require './Suggest.cjsx'
SubscribeButton = require './SubscribeButton.cjsx'
AnysearchActions = require '../../actions/AnysearchActions.coffee'
AnysearchStore = require '../../stores/AnysearchStore.coffee'
$ = require 'jquery'
_ = require 'underscore'


_get_state_from_store = () ->
  return {
    terms: AnysearchStore.get_terms()
    subscription_url: AnysearchStore.get_subscription_url()
    categories: AnysearchStore.get_categories()
    values: AnysearchStore.get_values()
    loading: AnysearchStore.is_loading()
  }


Searchbar = React.createClass

  getInitialState: () ->
    initial_state =
      active_term: null
      suggestion_type: null
    return _.extend(initial_state, _get_state_from_store())

  componentDidMount: () ->
    AnysearchStore.addChangeListener(@_onChange)
    $(document).click(@_handleGlobalClick)

  componentWillUnmount: () ->
    AnysearchStore.removeChangeListener(@_onChange)
    $(document).off('click')

  _event_was_inside_anysearch: (event) ->
    target_classname = $(event.target).attr('class')
    return target_classname?.startsWith('anysearch') or $.contains(@refs.searchbar, event.target)

  _handleGlobalClick: (event) ->
    if not @_event_was_inside_anysearch(event)
      # click happened ouside of anysearch
      @setState(
        active_term: null
        suggestion_type: null
      )

  onSuggestionSelected: (input) ->
    if @state.active_term?
      if @state.suggestion_type == 'category'
        AnysearchActions.changeTermCategory(@state.active_term.id, input)
        @setState({suggestion_type: 'value'})
      else
        AnysearchActions.changeTermValue(@state.active_term.id, input)
        @setState({suggestion_type: null})

  onSearchbarClicked: (event) ->
    if event.target == @refs.searchbar or event.target == @refs.icon or event.target == @refs.placeholder
      @refs.last_term.focus()

  onSubscribeClicked: (event) ->
    event.preventDefault()
    console.log AnysearchStore.get_subscription_url()
 


  render: ->
    last_key = @state.terms.length - 1
    terms = _.map(@state.terms, (term, key) =>
      if key == last_key
        last_term = "last_term"
      term_input_focused = (event, left) =>
        AnysearchActions.updateFacets(term.id)
        if term.helper
          type = 'category'
        else
          type = 'value'
        @setState({
          active_term: term,
          suggestion_type: type,
          suggestion_left_position: left
        })
      term_clicked = (event, left) =>
        AnysearchActions.updateFacets(term.id)
        @setState({
          active_term: term,
          suggestion_type: 'category',
          suggestion_left_position: left
        })
      <Term
        key={term.id}
        id={term.id}
        category={term.category}
        value={term.value}
        helper={term.helper}
        permanent={term.permanent}
        onTermClicked={term_clicked}
        onInputFocused={term_input_focused}
        ref={last_term}
      />
    )
    if @state.active_term
      switch @state.suggestion_type
        when 'value' then items = @state.values
        when 'category' then items = @state.categories
      if items and items.length > 0
        suggest = <Suggest
                    items={items}
                    onSelect={@onSuggestionSelected}
                    loading={@state.loading}
                    left={@state.suggestion_left_position}
                    ref="suggest"
                  />
    else if terms.length < 2
      placeholder = <span className="anysearch_placeholder" ref="placeholder">Wonach möchten Sie suchen?</span>
    <div className="anysearch_box" onClick={@onSearchbarClicked} ref="searchbar">
      <span className="anysearch_icon" ref="icon"></span>
      {placeholder}
      {terms}
      {suggest}
      <SubscribeButton subscription_url={@state.subscription_url} />
    </div>

  _onChange: () ->
    @setState(_get_state_from_store())

module.exports = Searchbar

