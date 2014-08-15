$(function(){
    $('#event-date').datepicker({
        inputs: $('#event-start, #event-end'),
        todayBtn: 'linked',
        format: 'dd/mm/yyyy'
    });

    $('#talk-date').datepicker({
        startDate: $('#start-date').text(),
        endDate: $('#end-date').text(),
        format: 'dd/mm/yyyy',
    });

    $('#talk-start').timepicker();

    $('#talk-end').timepicker();
});