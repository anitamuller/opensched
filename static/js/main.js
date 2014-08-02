window.MDM_SILENT = true;
$(function(){
    $('a[data-target="_blank"]').attr('target', '_blank');

    if($('#post-short').length && $('#post-full').length) {
        $('#post-short').mdmagick();
        $('#post-full').mdmagick();
    }

    $('.post .article img').each(function(index, el){
        var anchor = '<a href="'+$(el).attr('src')+'" title="'+$(el).attr('alt')+'" data-lightbox="'+$(el).attr('src')+'"><img src="'+$(el).attr('src')+'" alt="'+$(el).attr('alt')+'"></a>';
        $(el).replaceWith(anchor);
    });

    $('#post-preview').on('click', function(){
        var postForm = $('#post-form');
        postForm.find('#preview').val('1');
    });
    $('#post-submit').on('click', function(){
        var postForm = $('#post-form');
        postForm.find('#preview').val('');
    });
    $('a.icon').on('click', function(){
        return confirm('Are you sure?');
    });

    $('#event-date').datepicker({
        inputs: $('#event-start, #event-end, #talk-date'),
        todayBtn: 'linked'
    });

    $('#talk-start').timepicker();

    $('#talk-end').timepicker();


    it('should change state', function() {
        var value1 = element(by.binding('value1'));
        expect(value1.getText()).toContain('YES');
        element(by.model('value1')).click();
        expect(value1.getText()).toContain('NO');

    });


});
