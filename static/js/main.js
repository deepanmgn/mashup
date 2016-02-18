$(function () {

    $('#more').click(function(ev) {

        $("#results").css("opacity","0.3");

        $("#spinner").show();

        $.ajax({
            url : '/more',
            data : {},
            type : 'GET',
            success : function(data) {
                $("#results").css("opacity","1");
                if (data == "__last__") {
                    $("#more").hide();
                    $('#results').append('<div id="no_results"> No more results to display</div>')
                }
                else {
                    $('#results').append(data)
                }
                $("#spinner").hide();
                //make hidden
            },
            error : function(xhr, status) {
                alert("Some error Occurred");
            }
        });
    });
});
