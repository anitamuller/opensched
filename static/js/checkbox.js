$(function() {
     $('#select-all').on('click', function(){  //  on click
         if(this.checked) { // check select status
            $('.delete-item').each(function() {  //  loop through each checkbox
                this.checked = true;  //  select all checkboxes with class "delete-talk_checkbox"
            });
            }else{
                $('.delete-item').each(function() {  //  loop through each checkbox
                    this.checked = false;  //  deselect all checkboxes with class "delete-talk_checkbox"
                });
                }
    });
});


