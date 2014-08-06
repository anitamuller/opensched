window.MDM_SILENT = true;
$(function() {
    $('a[data-target="_blank"]').attr('target', '_blank');

    $('#event-preview').on('click', function() {
        var eventForm = $('#event-form');
        eventForm.find('#preview').val('1');
    });
    $('#event-submit').on('click', function() {
        var eventForm = $('#event-form');
        eventForm.find('#preview').val('');
    });

    $('#talk-preview').on('click', function() {
        var talkForm = $('#talk-form');
        talkForm.find('#preview').val('1');
    });

    $('#talk-submit').on('click', function() {
        var talkForm = $('#talk-form');
        talkForm.find('#preview').val('');
    });

    $('a.icon').on('click', function() {
        return confirm('Are you sure?');
    });
});