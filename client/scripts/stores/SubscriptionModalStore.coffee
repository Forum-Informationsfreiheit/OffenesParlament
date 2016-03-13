AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
EventEmitter = require('events').EventEmitter
Const = require('../constants/SubscriptionModalConstants.coffee')
assign = require('object-assign')
$ = require 'jquery'
_ = require 'underscore'
csrf_utils = require '../utils/csrf_token.coffee'


CHANGE_EVENT = 'change'

_show_modal = false
_subscription_url = ''
_subscription_title = ''
_server_status = Const.SERVER_STATUS_NEUTRAL
_email = ''


_query_server = () ->
  _server_status = Const.SERVER_STATUS_QUERYING
  $.ajax
    url: '/subscribe'
    method: 'POST'
    data:
      csrfmiddlewaretoken: csrf_utils.get_csrf_token()
      subscription_url: _subscription_url
      subscription_title: _subscription_title
      email: _email
    success: (response) ->
      _server_status = Const.SERVER_STATUS_SUCCESS
    error: (response) ->
      _server_status = Const.SERVER_STATUS_ERROR
    complete: () ->
      SubscriptionModalStore.emitChange()


SubscriptionModalStore = assign({}, EventEmitter.prototype, {

  is_modal_shown: () ->
    return _show_modal

  get_subscription_url: () ->
    return _subscription_url

  get_subscription_title: () ->
    return _subscription_title

  get_server_status: () ->
    return _server_status

  get_email: () ->
    return _email

  emitChange: () ->
    this.emit(CHANGE_EVENT)

  addChangeListener: (callback) ->
    this.on(CHANGE_EVENT, callback)

  removeChangeListener: (callback) ->
    this.removeListener(CHANGE_EVENT, callback)

  dispatcherIndex: AppDispatcher.register( (payload) =>
    switch payload.actionType
      when Const.ACTION_SHOW_MODAL
        _subscription_url = payload.subscription_url
        _subscription_title = payload.subscription_title
        _server_status = Const.SERVER_STATUS_NEUTRAL
        _show_modal = true
        SubscriptionModalStore.emitChange()
      when Const.ACTION_HIDE_MODAL
        _show_modal = false
        SubscriptionModalStore.emitChange()
      when Const.ACTION_SET_EMAIL
        _email = payload.email
        SubscriptionModalStore.emitChange()
      when Const.ACTION_SEND_DATA
        _query_server()
        SubscriptionModalStore.emitChange()
    return true # No errors. Needed by promise in Dispatcher.
  )
})


module.exports = SubscriptionModalStore
