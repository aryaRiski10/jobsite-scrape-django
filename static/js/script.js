$(document).ready(function() {
    $.ajax({
        url: "/home/jobs-search-api/",
        method: 'POST',
        data: {
            'keywordTitle': $('#keywordTitle').val(),
            'keywordLocation': $('#keywordLocation').val(),
        },
        success: function(datas) {
            for (i = 0; i < datas.length; i++) {
                data = datas[i].fields;
                console.log(data.fields);

                t = $('#template').clone();
                t.attr('id', 'job-' + i);
                t.removeClass('d-none');

                t.find('#job_title1').text(data.title);
                t.find('#job_title2').text(data.title);
                t.find('#job_image1').attr('src', data.image);
                t.find('#job_image2').attr('src', data.image);
                t.find('#job_company1').text(data.company);
                t.find('#job_company2').text(data.company);
                t.find('#job_location1').text(data.location);
                t.find('#job_location2').text(data.location);
                t.find('#job_requirement1').text(data.requirement);
                t.find('#job_link1').attr('href', data.link);
                t.find('#job_link2').attr('href', data.link);
                t.find('#job_datetime_posted1').text(data.datetime_posted);
                t.find('#job_datetime_posted2').text(data.datetime_posted);
                t.find('#job_datetime_posted3').text(data.datetime_posted);

                t.appendTo('#job_list');
            }
            // generate card dari filter data
        }
    })

    //kalau 3 hari dkk dicentang, ajax lagi

});