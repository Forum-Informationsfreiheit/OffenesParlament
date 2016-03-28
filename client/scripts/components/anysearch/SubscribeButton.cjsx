React = require 'react'
SubscriptionModalActions = require '../../actions/SubscriptionModalActions.coffee'
classnames = require 'classnames'


SubscribeButton = React.createClass

  _open_modal: (e) ->
    e.preventDefault()
    if @props.active
      SubscriptionModalActions.showModal(@props.subscription_url, @props.search_ui_url, @props.subscription_title, @props.subscription_category)

  render: ->
    htmlClassnames = classnames("anysearch_subscribe_button", {'active': @props.active})
    return <a
      href="#"
      className={htmlClassnames}
      onClick={@_open_modal}>Suche abonnieren</a>

module.exports = SubscribeButton

