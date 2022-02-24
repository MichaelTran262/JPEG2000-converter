Dropzone.options.myDropzone = {
    url: '/upload',
    autoProcessQueue: false,
    maxFilesize: 2048,
    createImageThumbnails: false,
    uploadMultiple: true,
    parallelUploads: 100,
    maxFiles: 30,
    acceptedFiles: '.jp2',
    //addRemoveLinks: true,
    dictDefaultMessage: 'Nahrajte nebo přetáhněte soubory tady<br> <p class="text-muted">Max 2GB pro jeden soubor</p>',

    init: function () {

        var submitButton = document.querySelector("#submit-all");
        var wrapperThis = this;

        submitButton.addEventListener("click", function () {
            form_data = new Object();
            form_data.title = $('#title').val();
            form_data.format = $('#sel_format').val();
            console.debug(JSON.stringify(form_data));
            jQuery.ajax({
                url: '/add_batch',
                type: 'POST',
                data: JSON.stringify(form_data),
                contentType: 'application/json; charset=utf-8',
                dataType: 'json',
                async: false,
                success: function (data) {
                    console.log("/add_batch")
                    $('#archive_content').empty()
                    for (var i = 0; i < data.length; i++)
                    {
                        var row = "";
                        row += '<td>' + data[i].name;
                        if(data[i].state == 'waiting') {
                            row += `<a href="#" data-toggle="tooltip" data-placement="top" title="Archiv se zpracovává a je ve stavu čekající" style="margin-left: 10px;">
                                        <i class="fa fa-info-circle" aria-hidden="true"></i>
                                    </a>
                                    <div class="spinner-border spinner-border-sm" style="margin-left: 10px;"></div>`
                            row += `</td>
                                    <td>
                                        <a href="/delete/${data[i].id}">
                                            <button class="btn btn-danger"><i class="fa fa-times"></i></button>
                                        </a>
                                    </td>`;
                            
                        } else if (data[i].state == 'exists') {
                            row += '</td>'
                            row += `<td>
                                    <a href="/batch/${data[i].name}">
                                        <button class="btn btn-primary"><i class="fa fa-download"></i></button>
                                    </a>
                                    <a href="/delete/${data[i].id}">
                                        <button class="btn btn-danger"><i class="fa fa-times"></i></button>
                                    </a>
                                    </td>`;
                        }
                        row += '<td>' + data[i].date_created + '</td>';
                        $('#archive_content').append('<tr>' + row + '</tr>');
                    }
                }
            });
            wrapperThis.processQueue();
        });

        this.on("addedfile", function (file) {

            // Create the remove button
            var removeButton = Dropzone.createElement("<button class='btn btn-link btn-sm'>Odstranit</button>");

            // Listen to the click event
            removeButton.addEventListener("click", function (e) {
                // Make sure the button click doesn't submit the form:
                e.preventDefault();
                e.stopPropagation();

                // Remove the file preview.
                wrapperThis.removeFile(file);
                // If you want to the delete the file on the server as well,
                // you can do the AJAX request here.
            });

            // Add the button to the file preview element.
            file.previewElement.appendChild(removeButton);
        });

        this.on('sendingmultiple', function (data, xhr, formData) {
            formData.append("title", $("#title").val());
            formData.append("format", $("#format").val());
            formData.append("program", $("#program").val());
        });
        this.on("successmultiple", function(files, response) {
            $('.dz-preview').empty();
            jQuery.ajax({
                url: '/api/table',
                type: 'GET',
                contentType: 'application/json; charset=utf-8',
                dataType: 'json',
                async: false,
                success: function (data) {
                    console.log("/api/table")
                    $('#archive_content').empty()
                    for (var i = 0; i < data.length; i++)
                    {
                        var row = "";
                        row += '<td>' + data[i].name;
                        if(data[i].state == 'waiting') {
                            row += `<a href="#" data-toggle="tooltip" data-placement="top" title="Archiv se zpracovává a je ve stavu čekající" style="margin-left: 10px;">
                                        <i class="fa fa-info-circle" aria-hidden="true"></i>
                                    </a>
                                    <div class="spinner-border spinner-border-sm" style="margin-left: 10px;"></div>`
                            row += '</td>';
                        
                        } else if (data[i].state == 'exists') {
                            row += '</td>'
                            row += `<td>
                                    <a href="/batch/${data[i].name}">
                                        <button class="btn btn-primary"><i class="fa fa-download"></i></button>
                                    </a>
                                    <a href="/delete/${data[i].id}">
                                        <button class="btn btn-danger"><i class="fa fa-times"></i></button>
                                    </a>
                                    </td>`;
                        }
                        row += '<td>' + data[i].date_created + '</td>';
                        $('#archive_content').append('<tr>' + row + '</tr>');
                    }
                }
            });
        });
        this.on("errormultiple", function(files, response) {

        });
    }
};