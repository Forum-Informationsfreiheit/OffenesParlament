React = require 'react'


_get_state_from_store = () ->
  return {
    results: AnysearchStore.get_search_results()
  }


SearchApp = React.createClass

  getInitialState: () ->
    return _get_state_from_store()

  componentDidMount: () ->
    AnysearchStore.addChangeListener(@_onChange)

  componentWillUnmount: () ->
    AnysearchStore.removeChangeListener(@_onChange)

  render: ->
    results = @props.results.map (r) =>
      if r.title?
        return <li>{r.title}</li>
      else if r.full_name?
        return <li>{r.full_name}</li>
    <ul>{results}</ul>

module.exports = SearchApp

