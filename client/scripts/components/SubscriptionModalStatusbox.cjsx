React = require 'react'
SubscriptionModalActions = require '../actions/SubscriptionModalActions.coffee'
Spinner = require 'react-spin'
Const = require('../constants/SubscriptionModalConstants.coffee')


spinCnfg =
  lines: 11  # The number of lines to draw
  length: 3  # The length of each line
  width: 3  # The line thickness
  radius: 6  # The radius of the inner circle
  corners: 1  # Corner roundness (0..1)
  rotate: 0  # The rotation offset
  direction: 1  # 1: clockwise  -1: counterclockwise
  color: '#7f7f7f'  # #rgb or #rrggbb or array of colors
  speed: 1.2  # Rounds per second
  trail: 100  # Afterglow percentage
  shadow: false  # Whether to render a shadow
  hwaccel: false  # Whether to use hardware acceleration
  className: 'spinner'  # The CSS class to assign to the spinner
  zIndex: 2e9  # The z-index (defaults to 2000000000)
  top: '50%'  # Top position relative to parent
  left: '50%' # Left position relative to parent
  position: 'relative'


SubscriptionModalStatusbox = React.createClass

  _on_cancel_clicked: (e) ->
    e.preventDefault()
    SubscriptionModalActions.hideModal()

  render: ->
    switch @props.server_status
      when Const.SERVER_STATUS_QUERYING
        message = <p>Ihr Abo für <b>{@props.subscription_title}</b> wird eingerichtet.</p>
        status_icon = <div className="spinner_container"><Spinner config={spinCnfg} /></div>
      when Const.SERVER_STATUS_SUCCESS
        message = <p>Ihr Abo für <b>{@props.subscription_title}</b> wurde eingerichtet. Sie erhalten nun ein Bestätigungs-E-Mail um Ihre E-Mail-Adresse zu bestätigen.</p>
        status_icon = <div className="status_icon_success"></div>
      when Const.SERVER_STATUS_ERROR
        message = <p>Ihr Abo für <b>{@props.subscription_title}</b> konnte nicht eingerichtet werden. Bitte versuchen Sie es erneut.</p>
        status_icon = <div className="status_icon_error"></div>
    return <div>
        <h2>Benachrichtigungen abonnieren</h2>
        {message}
        {status_icon}
        <div className="buttons">
          <a href="#" className="button_large button_cancel" onClick={@_on_cancel_clicked}>Schließen</a>
        </div>
      </div>

module.exports = SubscriptionModalStatusbox

