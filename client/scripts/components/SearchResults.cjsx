React = require 'react'


SearchResults = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  render: ->
    results = _.map(@props.results, (r) =>
      if r.title?
        return <li key={r.title}>{r.title}</li>
      else if r.full_name?
        return <li key={r.full_name}><a href={r.internal_link}>{r.full_name}</a></li>
    )
    <div>
      <div className="top_bar"></div>
      <h1>Suchergebnisse</h1>
      <p className="explanation">
      Hier finden Sie eine Übersicht über alle Abgeordneten zum Nationalrat in
      der aktuellen Gesetzgebungsperiode (XXV.). Um eine genauere Auswahl zu
      treffen, benutzen Sie die Suche.
      </p>
      <ul>{results}</ul>
    </div>

module.exports = SearchResults

