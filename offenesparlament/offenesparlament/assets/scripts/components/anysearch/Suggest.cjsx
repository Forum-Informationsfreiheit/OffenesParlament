React = require 'react'
SuggestItem = require './SuggestItem.cjsx'


Suggest = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  render: ->
    autocomplete_styles = {position: 'absolute', backgroundColor: 'wheat'}
    items = _.map(@props.items, (item) =>
      on_item_selected = () =>
        @props.onSelect(item)
      <SuggestItem key={item} text={item} onClick={on_item_selected} />
    )
    <div style={autocomplete_styles}>{items}</div>

module.exports = Suggest
