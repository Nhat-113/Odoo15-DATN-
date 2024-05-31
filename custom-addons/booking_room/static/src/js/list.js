odoo.define("booking_room.room_view_tree", function (require) {
  "use strict";
  var ListRenderer = require("web.ListRenderer");
  var viewRegistry = require("web.view_registry");
  var ListView = require('web.ListView');


  var CustomListRenderer = ListRenderer.extend({
    _renderBody: function () {
      var self = this;
      var $rows = this._renderRows();
      while ($rows.length < 4) {
        $rows.push(self._renderEmptyRow());
      }

      // Add row numbers
      var rowNumber = 1;
      $rows.forEach(function ($row) {
        var $cells = $row.children();
        $('<td class="o_data_cell">')
          .text(rowNumber)
          .insertAfter($cells.first());
        rowNumber++;
      });

      return $("<tbody>").append($rows);
    },

    _renderHeader: function (isGrouped) {
      var $tr = $("<tr>").append(
        _.map(this.columns, this._renderHeaderCell.bind(this))
      );
      if (this.hasSelectors) {
        $tr.prepend(this._renderSelector("th"));
      }
      $('<th class="o_column_sortable">No.</th>').insertAfter(
        $tr.find("th").first()
      ); // Add header for row numbers in the second column
      return $("<thead>").append($tr);
    },
  });

  var CustomBasicView = ListView.extend({
    config: Object.assign({}, ListView.prototype.config, {
      Renderer: CustomListRenderer,
    }),
  });

  viewRegistry.add("list_view", CustomBasicView);
});
