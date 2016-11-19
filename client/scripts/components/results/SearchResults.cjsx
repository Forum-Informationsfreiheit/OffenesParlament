React = require 'react'
SubscriptionModalActions = require '../../actions/SubscriptionModalActions.coffee'
SearchResultsRow = require './SearchResultsRow.cjsx'
Pagination = require './Pagination.cjsx'
ResultsPreview = require '../anysearch/ResultsPreview.cjsx'
_ = require 'underscore'
classnames = require 'classnames'
AnysearchConstants = require '../../constants/AnysearchConstants.coffee'


SearchResults = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  _open_subscription_modal: (e) ->
    e.preventDefault()
    if @props.allow_subscription
      SubscriptionModalActions.showModal(@props.subscription_url, @props.search_ui_url, @props.subscription_title)

  render: ->
    htmlClassnames = classnames('button', 'button_notifications', 'disabled': !@props.allow_subscription)
    if @props.results.length > 0
      result_rows = _.map(@props.results, (r) =>
        title = if r.title? then r.title else r.full_name
        key = if r.parl_id? then r.parl_id else r.llp + ";" + r.nr
        date = if r.ts? then r.ts else r.date
        if r.debate_type? and r.debate_type == 'NR'
          title += ' des Nationalrats'
        else if r.debate_type? and r.debate_type == 'BR'
          title += ' des Bundesrats'
        return <SearchResultsRow title={title} url={r.internal_link} date={date} key={key} />
      )
      search_results = <table className="search_results">
          <thead>
            <tr>
              <th>Aktualisierung</th>
              <th>Titel / Name</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {result_rows}
          </tbody>
        </table>
    else
      search_results = <p className="explanation">Zu Ihrer Suche wurden keine Ergebnisse gefunden.</p>
    if @props.subscription_prohibited_reason == AnysearchConstants.SUBSCRIPTION_PROHIBITED_REASON_NO_LLP
      subscription_prohibited_explanation = <span>Bitte wählen Sie eine Gesetzgebungsperiode aus um die Suche zu abonnieren.</span>
    else if @props.subscription_prohibited_reason == AnysearchConstants.SUBSCRIPTION_PROHIBITED_REASON_NEED_MORE_FACETS
      subscription_prohibited_explanation = <span>Bitte wählen Sie weitere Filter aus um die Suche zu abonnieren.</span>
    <div>
      <div className="top_bar">
        <ul className="breadcrumbs">
          <li><a href="/">Startseite</a></li>
          <li>Suche</li>
        </ul>
      </div>
      <div className="title_with_button">
        <h1>Suchergebnisse</h1>
        <a href="#" className={htmlClassnames}
          onClick={@_open_subscription_modal}>Benachrichtigung aktivieren</a>
      </div>
      <p>
        <ResultsPreview result_count={@props.pagination.offset} /> {subscription_prohibited_explanation}
      </p>
      {search_results}
      <Pagination
        offset={@props.pagination.offset}
        items_per_page={@props.pagination.items_per_page}
        max_items={@props.pagination.max_items}
      />
    </div>

module.exports = SearchResults

