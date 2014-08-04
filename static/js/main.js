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
        todayBtn: 'linked',
        format: 'dd/mm/yyyy'
    });

    $('#talk-start').timepicker();

    $('#talk-end').timepicker();


    $('#select-all').on('click', function() {  //on click
        if(this.checked) { // check select status
            $('.delete-talk').each(function() { //loop through each checkbox
                this.checked = true;  //select all checkboxes with class "delete-talk_checkbox"
            });
            }else{
                $('.delete-talk').each(function() { //loop through each checkbox
                    this.checked = false; //deselect all checkboxes with class "delete-talk_checkbox"
                });
                }
    });

});
