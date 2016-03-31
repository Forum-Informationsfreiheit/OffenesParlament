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
    if date_string == '01.01.1970'
      date_string = ''
    <tr>
      <td>{date_string}</td>
      <td><a href={@props.url}>{@props.title}</a></td>
      <td>{@props.status}</td>
    </tr>

module.exports = SearchResultsRow

