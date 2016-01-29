React = require 'react'
Modal = require('react-overlays').Modal


SubscriptionModal = React.createClass

  getInitialState: () ->
    return { show: false }

  # componentDidMount: () ->
  #   window.setTimeout(() =>
  #     @setState({show: true})
  #   , 2000)

  render: ->
    return <div>
        <Modal
          show={@state.show}
          backdropClassName="subscription_modal_backdrop"
          className="subscription_modal">
          <div className="subscription_modal_dialog">
            <h2>FOOBAR</h2>
          </div>
        </Modal>
      </div>

module.exports = SubscriptionModal

