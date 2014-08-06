$(function(){
    $('#event-date').datepicker({
        inputs: $('#event-start, #event-end, #talk-date'),
        todayBtn: 'linked',
        format: 'dd/mm/yyyy'
    });

    $('#talk-start').timepicker();

    $('#talk-end').timepicker();
});