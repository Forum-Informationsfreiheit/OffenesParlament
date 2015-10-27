React = require 'react'
AutosizeInput = require('react-input-autosize');
AnysearchActions = require '../../actions/AnysearchActions.coffee'
StringUtils = require '../../utils/StringUtils.coffee'


Term = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  onChange: (event) ->
    AnysearchActions.changeTermValue(@props.id, event.target.value)

  render: ->
    <span key={@props.id}>
      <span onClick={@props.onTermClicked}>{StringUtils.get_category_text(@props.category)}</span>
      <AutosizeInput
          name="form-field-name"
          value={@props.value}
          onChange={@onChange}
          onFocus={@props.onInputFocused}
      />
    </span>

module.exports = Term

