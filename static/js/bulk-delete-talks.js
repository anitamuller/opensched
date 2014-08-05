
    var formApp = angular.module('formApp', []);

    function talksController($scope, $http) {
        $scope.showButtonTrash = false;

        $scope.clickDelete = function() {
            trash = false
            $('.delete-talk').each(function() {  // loop through each checkbox
                if (this.checked) trash = true;
            });
            $scope.showButtonTrash = trash
        };

        $scope.talksToDelete = function() {
            talk_list = []
            $('.delete-talk').each(function() {  // loop through each checkbox
                if (this.checked)
                    talk_list.push(this.value)
            });

            $.ajax({
                url: 'http://localhost:8080/bulk_delete_talks',
                type: 'POST',
                data: JSON.stringify({ talks_to_remove: talk_list }),
                contentType: "application/json; charset=utf-8",
            });
        };
    }