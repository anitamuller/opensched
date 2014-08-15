var singleTalk = angular.module('singleTalk', []);

function talkController($scope) {
    $scope.showAttendees = true;

    $scope.clickAttendees = function() {
        if ($scope.showAttendees == false) {
            $scope.showAttendees = !$scope.showAttendees;
        }
    }
};