React = require 'react'
AutosizeInput = require('react-input-autosize');
AnysearchActions = require '../../actions/AnysearchActions.coffee'
StringUtils = require '../../utils/StringUtils.coffee'
classNames = require 'classnames'
$ = require 'jquery'
ReactDOM = require 'react-dom'


Term = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  onChange: (event) ->
    AnysearchActions.changeTermValue(@props.id, event.target.value)

  focus: () ->
    @refs.input.focus()

  render: ->
    cl_names = classNames({
      anysearch_term: true
      anysearch_term_helper: @props.helper
      anysearch_term_permanent: @props.permanent
    })
    if not @props.helper and not @props.permanent
      delete_button = <span onClick={@_on_delete_button_click} className="anysearch_term_delete_button">x</span>
    if @props.category
      category = <span onClick={@_on_term_clicked} className="anysearch_term_category" ref="category">{StringUtils.get_category_text(@props.category)}</span>
    <span key={@props.id} className={cl_names}>
      {delete_button}
      {category}
      <AutosizeInput
          name="form-field-name"
          value={@props.value}
          onChange={@onChange}
          onFocus={@_on_input_focused}
          minWidth=10
          className="anysearch_term_value"
          ref="input"
      />
    </span>

  _on_delete_button_click: (event) ->
    AnysearchActions.deleteTerm(@props.id)

  _get_left_offset: (ref) ->
    offset = $(ReactDOM.findDOMNode(ref)).offset()
    if offset and offset.left
      return offset.left
    else
      return null

  _on_term_clicked: (event) ->
    if not @props.permanent
      @props.onTermClicked(event, @_get_left_offset(@refs.category))

  _on_input_focused: (event) ->
    @props.onInputFocused(event, @_get_left_offset(@refs.input))

module.exports = Term

