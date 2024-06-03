odoo.define("booking_room.room_view_tree", function (require) {
  "use strict";
  var ListRenderer = require("web.ListRenderer");
  var viewRegistry = require("web.view_registry");
  var ListView = require("web.ListView");

  var CustomListRenderer = ListRenderer.extend({
    _renderBody: function () {
      var self = this;
      var $rows = this._renderRows();
      while ($rows.length < 4) {
        $rows.push(self._renderEmptyRow());
      }

      // Add row numbers only to non-empty rows
      var rowNumber = 1;
      $rows.forEach(function ($row) {
        // Check if the row has any non-empty cells
        var hasData = $row
          .children()
          .toArray()
          .some(function (cell) {
            return $(cell).text().trim() !== "";
          });
        if (hasData) {
          var $cells = $row.children();
          $('<td class="o_data_cell">')
            .text(rowNumber)
            .insertAfter($cells.first());
          rowNumber++;
        }
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

    _renderFooter: function () {
      var aggregates = {};
      _.each(this.columns, function (column) {
        if ("aggregate" in column) {
          aggregates[column.attrs.name] = column.aggregate;
        }
      });
      var $cells = this._renderAggregateCells(aggregates);
      if (this.hasSelectors) {
        $cells.unshift($("<td>"));
      }
      $cells.push($("<td>"));
      return $("<tfoot>").append($("<tr>").append($cells));
    },
  });

  var CustomBasicView = ListView.extend({
    config: Object.assign({}, ListView.prototype.config, {
      Renderer: CustomListRenderer,
    }),
  });

  viewRegistry.add("list_view", CustomBasicView);
});
