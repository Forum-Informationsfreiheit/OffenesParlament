AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
Const = require('../constants/SubscriptionModalConstants.coffee')


SubscriptionModalActions =
  showModal: (subscription_url, subscription_title) ->
    AppDispatcher.dispatch({
      actionType: Const.ACTION_SHOW_MODAL
      subscription_url: subscription_url
      subscription_title: subscription_title
    })

  hideModal: () ->
    AppDispatcher.dispatch({
      actionType: Const.ACTION_HIDE_MODAL
    })

  setEmail: (email) ->
    AppDispatcher.dispatch({
      actionType: Const.ACTION_SET_EMAIL
      email: email
    })

  sendData: () ->
    AppDispatcher.dispatch({
      actionType: Const.ACTION_SEND_DATA
    })


module.exports = SubscriptionModalActions
