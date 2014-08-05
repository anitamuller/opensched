
    var formApp = angular.module('formApp', []);

    function eventsController($scope, $http) {
        $scope.showButtonTrash = false;

        $scope.clickDelete = function() {
            trash = false
            $('.delete-event').each(function() {  // loop through each checkbox
                if (this.checked) trash = true;
            });
            $scope.showButtonTrash = trash
        };

        $scope.eventsToDelete = function() {
            event_list = []
            $('.delete-event').each(function() {  // loop through each checkbox
                if (this.checked)
                    talk_list.push(this.value)
            });

            $.ajax({
                url: 'http://localhost:8080/bulk_delete_events',
                type: 'POST',
                data: JSON.stringify({ events_to_remove: event_list }),
                contentType: "application/json; charset=utf-8",
            });
        };
    }