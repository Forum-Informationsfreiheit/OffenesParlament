React = require 'react'

Main = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  render: ->
    results = @props.results.map (r) =>
      if r.title?
        return <li>{r.title}</li>
      else if r.full_name?
        return <li>{r.full_name}</li>
    <ul>{results}</ul>

module.exports = Main

