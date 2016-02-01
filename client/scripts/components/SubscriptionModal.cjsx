React = require 'react'
Modal = require('react-overlays').Modal
SubscriptionModalForm = require './SubscriptionModalForm.cjsx'
SubscriptionModalStatusbox = require './SubscriptionModalStatusbox.cjsx'
SubscriptionModalActions = require '../actions/SubscriptionModalActions.coffee'
Const = require('../constants/SubscriptionModalConstants.coffee')


SubscriptionModal = React.createClass

  render: ->
    if @props.server_status == Const.SERVER_STATUS_NEUTRAL
      content = <SubscriptionModalForm email={@props.email} subscription_title={@props.subscription_title} />
    else
      content = <SubscriptionModalStatusbox server_status={@props.server_status} subscription_title={@props.subscription_title} />
    return <Modal
        show={@props.show}
        onHide={SubscriptionModalActions.hideModal}
        backdropClassName="subscription_modal_backdrop"
        className="subscription_modal"
      >
        <div className="subscription_modal_dialog">
          {content}
        </div>
      </Modal>

module.exports = SubscriptionModal

