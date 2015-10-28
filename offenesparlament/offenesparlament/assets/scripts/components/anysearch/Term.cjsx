React = require 'react'
AutosizeInput = require('react-input-autosize');
AnysearchActions = require '../../actions/AnysearchActions.coffee'
StringUtils = require '../../utils/StringUtils.coffee'
classNames = require 'classnames'


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
    cl_names = classNames({
      anysearch_term: true
      anysearch_term_helper: @props.helper
    })
    <span key={@props.id} className={cl_names}>
      <span onClick={@props.onTermClicked} className="anysearch_term_category">{StringUtils.get_category_text(@props.category)}</span>
      <AutosizeInput
          name="form-field-name"
          value={@props.value}
          onChange={@onChange}
          onFocus={@props.onInputFocused}
          minWidth=10
          className="anysearch_term_value"
      />
    </span>

module.exports = Term

