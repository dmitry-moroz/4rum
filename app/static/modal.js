$(document).ready(function() {
    var formErrors = $('#modalMeta').data('errors');
    if (Object.keys(formErrors).length !== 0) {
        $('#editCommentModal').modal();
    }
});
$(document).on("click", ".open-editCommentModal", function () {
     var commentBody = $(this).data('body');
     var commentAct = $(this).data('act');
     $(".modal-body #edit-comment-body").val(commentBody);
     $(".form").attr('action', commentAct);
});