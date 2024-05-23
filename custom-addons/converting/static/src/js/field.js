/** @odoo-module */

import basicFields from "web.basic_fields";
import basicController from "web.BasicController";

var { Markup } = require("web.utils");
var core = require("web.core");
var _t = core._t;
var modelName = "accounting.converting";

basicController.include({
  _notifyInvalidFields: function (invalidFields) {
    var record = this.model.get(this.handle, { raw: true });
    var fields = record.fields;
    if (this.modelName === modelName) {
      var warnings = invalidFields.map(function (fieldName, index) {
        var fieldStr = fields[fieldName].string;
        var isLastField = index === invalidFields.length - 1;
        return _.str.sprintf(
          "%s%s",
          _.escape(fieldStr),
          isLastField ? "" : "/ "
        );
      });
      if (warnings.length > 1) {
        warnings.unshift("The fields ");
        warnings.push(" are required");
      } else {
        warnings.unshift("The field ");
        warnings.push(" is required");
      }
      warnings.unshift("<ul>");
      warnings.push("</ul>");
      this.displayNotification({
        message: Markup(warnings.join("")),
        type: "danger",
      });
    } else {
      var warnings = invalidFields.map(function (fieldName) {
        var fieldStr = fields[fieldName].string;
        return _.str.sprintf("<li>%s</li>", _.escape(fieldStr));
      });
      warnings.unshift("<ul>");
      warnings.push("</ul>");
      this.displayNotification({
        title: _t("Invalid fields:"),
        message: Markup(warnings.join("")),
        type: "danger",
      });
    }
  },
});

basicFields.FieldBinaryFile.include({
  on_file_uploaded: function (size, name) {
    const handleAppend = (parentElement, className) => {
      var fileNameDiv = document.createElement("div");
      fileNameDiv.classList.add(className, "p-2");
      fileNameDiv.textContent = name;
      parentElement.innerHTML = "";
      parentElement.appendChild(fileNameDiv);
    };
    if (this.field.name === "invoice_attachment") {
      var parentElement = document.querySelector(".invoice-upload-container");
      handleAppend(parentElement, "invoice-file-name");
    }
    if (this.field.name === "ct_transaction_attachment") {
      var containers = document.querySelectorAll(".ct-upload-container");
      var parentElement = containers[containers.length - 2];
      handleAppend(parentElement, "ct-file-name");
    }
    if (this.field.name === "ck_transaction_attachment") {
      var containers = document.querySelectorAll(".ck-upload-container");
      var parentElement = containers[containers.length - 1];
      handleAppend(parentElement, "ck-file-name");
    }

    if (size === false) {
      this.displayNotification({
        message: _t("There was a problem while uploading your file"),
        type: "danger",
      });
      console.warn("Error while uploading file : ", name);
    } else {
      this.on_file_uploaded_and_valid.apply(this, arguments);
    }
    this.$(".o_form_binary_progress").hide();
    this.$("button").show();
  },

  _clearFile: function () {
    var self = this;
    this.$(".o_input_file").val("");
    this.set_filename("");

    if (this.model === modelName) {
      if (this.field.name === "invoice_attachment") {
        var parentElement = document.querySelector(".invoice-upload-container");
        parentElement.innerHTML = "";
      }
      if (this.field.name === "ct_transaction_attachment") {
        var containers = document.querySelectorAll(".ct-upload-container");
        var parentElement = containers[containers.length - 2];
        parentElement.innerHTML = "";
      }
      if (this.field.name === "ck_transaction_attachment") {
        var containers = document.querySelectorAll(".ck-upload-container");
        var parentElement = containers[containers.length - 1];
        parentElement.innerHTML = "";
      }
    }

    if (!this.isDestroyed()) {
      this._setValue(false).then(function () {
        self._render();
      });
    }
  },
});
