React = require 'react'
SubscriptionModalActions = require '../actions/SubscriptionModalActions.coffee'


SubscriptionModalForm = React.createClass

  _on_email_changed: (event) ->
    SubscriptionModalActions.setEmail(event.target.value)

  _on_cancel_clicked: (e) ->
    e.preventDefault()
    SubscriptionModalActions.hideModal()

  _on_ok_clicked: (e) ->
    e.preventDefault()
    SubscriptionModalActions.sendData()

  render: ->
    return <div>
        <h2>Benachrichtigungen abonnieren</h2>
        <p>Bitte senden Sie mir Aktualisierungen für <b>{@props.subscription_title}</b> an folgende E-Mail-Adresse:</p>
        <input
          type="text"
          placeholder="Meine E-Mail-Adresse"
          onChange={@_on_email_changed}
          value={@props.email}
        />
        <div className="buttons">
          <a href="#" className="button_large button_cancel" onClick={@_on_cancel_clicked}>Abbrechen</a>
          <a href="#" className="button_large button_ok" onClick={@_on_ok_clicked}>Abonnieren</a>
          <p className="info_text">Wir speichern Ihre E-Mail-Adresse
          ausschließlich um Ihnen Aktualisierungen zu senden und geben diese
          keinesfalls an Dritte weiter.</p>
        </div>
      </div>

module.exports = SubscriptionModalForm

