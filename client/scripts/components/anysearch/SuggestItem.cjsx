React = require 'react'
StringUtils = require '../../utils/StringUtils.coffee'


SuggestItem = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  render: ->
    <div className="anysearch_suggestions_item" onClick={@props.onClick} >{StringUtils.get_category_text(@props.text)}</div>

module.exports = SuggestItem

