function run_action(route, data, done) {
    $.post(route, data, done);
}

function update_plot(id) {
    $.get('/component', {id: id}, function(data) {
        $('#' + id).html(data);
    });
}

function search_for_kw(kw) {
    run_action('search-for-kw', {kw: kw}, function() {
        update_plot('nresults-div');
        update_plot('res-table');
        update_plot('bar-chart');
        update_plot('heatmap');
        update_plot('comp-div');
    })
}

function select_res(index) {
    run_action('select-res', {index: index}, function() {
        update_plot('bar-chart');
        update_plot('comp-div');
    })
}

function select_bar(index) {
    run_action('select-bar', {index: index}, function() {
        update_plot('comp-div');
    })
}

function select_hm_cell(uuid_x, uuid_y) {
    run_action('select-hm-cell', {uuid_x: uuid_x, uuid_y: uuid_y}, function() {
        update_plot('comp-div');
    })
}

function toggle_cs_only() {
    cs_only = $('#cs-only').is(":checked")
    run_action('toggle-cs-only', {cs_only: cs_only}, function() {
        update_plot('heatmap');
        update_plot('bar-chart');
    })

}

$(document).ready(function(){
    search_for_kw('')
});
