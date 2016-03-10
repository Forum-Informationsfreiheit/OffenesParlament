React = require 'react'
SubscriptionModalActions = require '../actions/SubscriptionModalActions.coffee'
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
    SubscriptionModalActions.showModal(@props.subscription_url, @props.subscription_title)

  render: ->
    results = _.map(@props.results, (r) =>
      if r.title?
        return <li key={r.parl_id}><a href={r.internal_link}>{r.title}</a></li>
      else if r.full_name?
        return <li key={r.parl_id}><a href={r.internal_link}>{r.full_name}</a></li>
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
      <ul>{results}</ul>
    </div>

module.exports = SearchResults

