function fillRandomNumbers(rangeA1) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getRange(rangeA1);
  var numRows = range.getNumRows();
  var numCols = range.getNumColumns();
  var values = [];
  for (var r = 0; r < numRows; r++) {
    var row = [];
    for (var c = 0; c < numCols; c++) {
      row.push(Math.random());
    }
    values.push(row);
  }
  range.setValues(values);
}
