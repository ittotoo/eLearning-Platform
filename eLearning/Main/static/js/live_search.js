$(document).ready(function() {
    $('#live-search').keyup(function() {
        var query = $(this).val();
        var searchURL = $(this).data('search-url'); // Use the URL from the data attribute
        if (query.length > 2) {
            $.ajax({
                url: searchURL,
                data: {'query': query},
                success: function(data) {
                    $('#live-search-results').html(data);
                }
            });
        } else {
            $('#live-search-results').html('');
        }
    });
});