var KW = 'kw'
var SELECTED_RES_INDEX = 'selected_res_index'
var COMPARED_BASE = 'compared_base'
var COMPARED_BASE_BAR = 'bar'
var COMPARED_BASE_HM = 'hm'
var SELECTED_BAR_INDEX = 'selected_bar_index'
var SELECTED_HM_X = 'selected_hm_x'
var SELECTED_HM_Y = 'selected_hm_y'
var CS_ONLY = 'cs_only'
var SIM = 'sim'

var _data = {}

function run_action(route, data, done) {
    $.post(route, data, done);
}

function update_plot(id) {
    payload = $.extend({}, _data);
    payload['id'] = id

    $.get('/component', payload, function(data) {
        $('#' + id).html(data);
    });
}

function open_qcomparison(uuid_x, uuid_y, sim, in_new=true) {
    params = {};
    params[SELECTED_HM_X] = uuid_x;
    params[SELECTED_HM_Y] = uuid_y;
    params[SIM] = sim;

    window.open("/qcompare?" + jQuery.param(params), in_new ? null : "_self");
}

function open_qcomparison_from_bar(cb_obj, src, sim) {
    var i = Math.round(cb_obj['x']);
    var uuid_x = src.data['uuid_x'][i];
    var uuid_y = src.data['uuid_y'][i];

    open_qcomparison(uuid_x, uuid_y, sim);
}

function open_qcomparison_from_hm(uuid_x, uuid_y, sim) {
    open_qcomparison(uuid_x, uuid_y, sim);
}

function search_for_kw(kw) {
    _data[KW] = kw
    delete _data[SELECTED_RES_INDEX]

    update_plot('nresults-div');
    update_plot('res-table');
    update_plot('bar-chart');
    update_plot('heatmap');
}

function select_res(index) {
    _data[SELECTED_RES_INDEX] = index

    update_plot('bar-chart');
}

function select_bar(index) {
    _data[COMPARED_BASE] = COMPARED_BASE_BAR
    _data[SELECTED_BAR_INDEX] = index

    update_plot('comp-div');
}

function select_hm_cell(uuid_x, uuid_y) {
    _data[COMPARED_BASE] = COMPARED_BASE_HM
    _data[SELECTED_HM_X] = uuid_x
    _data[SELECTED_HM_Y] = uuid_y

    update_plot('comp-div');
}

function toggle_cs_only() {
    _data[CS_ONLY] = $('#cs-only').is(":checked")
    delete _data[COMPARED_BASE]

    update_plot('heatmap');
    update_plot('bar-chart');
}

$(document).ready(function(){
    search_for_kw('')
});
