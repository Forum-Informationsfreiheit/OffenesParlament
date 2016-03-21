React = require 'react'
_ = require 'underscore'
string_utils = require '../../utils/StringUtils.coffee'


SearchResultsRow = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  render: ->
    date_string = string_utils.get_date(@props.date)
    <tr>
      <td>{date_string}</td>
      <td><a href={@props.url}>{@props.title}</a></td>
      <td>{@props.status}</td>
    </tr>

module.exports = SearchResultsRow

