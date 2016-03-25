React = require 'react'
SubscriptionModalActions = require '../../actions/SubscriptionModalActions.coffee'
SearchResultsRow = require './SearchResultsRow.cjsx'
_ = require 'underscore'


SearchResults = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  _open_subscription_modal: (e) ->
    e.preventDefault()
    SubscriptionModalActions.showModal(@props.subscription_url, @props.search_ui_url, @props.subscription_title)

  render: ->
    results = _.map(@props.results, (r) =>
      title = if r.title? then r.title else r.full_name
      key = if r.parl_id? then r.parl_id else r.llp + ";" + r.nr
      return <SearchResultsRow title={title} url={r.internal_link} date={r.ts} key={key} />
    )
    <div>
      <div className="top_bar">
        <ul className="breadcrumbs">
          <li><a href="/">Startseite</a></li>
          <li>Suche</li>
        </ul>
      </div>
      <div className="title_with_button">
        <h1>Suchergebnisse</h1>
        <a href="#" className="button button_notifications"
          onClick={@_open_subscription_modal}>Benachrichtigung aktivieren</a>
      </div>
      <table className="search_results">
        <thead>
          <tr>
            <th>Aktualisierung</th>
            <th>Titel / Name</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {results}
        </tbody>
      </table>
    </div>

module.exports = SearchResults

