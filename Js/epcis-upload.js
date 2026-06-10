let selectedFile = null;

function incrementDashboardStat(key){

    const stats =
    JSON.parse(
        localStorage.getItem(
            "dashboardStats"
        ) || "{}"
    );

    stats[key] =
    (stats[key] || 0) + 1;

    localStorage.setItem(
        "dashboardStats",
        JSON.stringify(stats)
    );
}

function loadProfiles(){

    const profiles =
    JSON.parse(
        localStorage.getItem(
            "profiles"
        ) || "[]"
    );

    const profileSelect =
    document.getElementById(
        "profileSelect"
    );

    const sftpProfileSelect =
    document.getElementById(
        "sftpProfileSelect"
    );

    profileSelect.innerHTML =
    `
    <option value="">
        Select Profile
    </option>
    `;

    if(sftpProfileSelect){

        sftpProfileSelect.innerHTML =
        `
        <option value="">
            Select Profile
        </option>
        `;
    }

    profiles
    .filter(
        profile =>

        profile.module ===
        "EPCIS_UPLOAD"

        &&

        profile.active
    )
    .forEach(
        profile => {

            if(
                profile.connectionType ===
                "HTTPS"
            ){

                const option =
                document.createElement(
                    "option"
                );

                option.value =
                profile.id;

                option.textContent =
                profile.profileName;

                profileSelect.appendChild(
                    option
                );
            }

            if(
                profile.connectionType ===
                "SFTP"
                &&
                sftpProfileSelect
            ){

                const option =
                document.createElement(
                    "option"
                );

                option.value =
                profile.id;

                option.textContent =
                profile.profileName;

                sftpProfileSelect.appendChild(
                    option
                );
            }
        }
    );
}

/* Controls */

const transferType =
document.getElementById(
    "transferType"
);

const fileInput =
document.getElementById(
    "xmlFile"
);

const uploadButton =
document.getElementById(
    "uploadButton"
);

const clearButton =
document.getElementById(
    "clearButton"
);

/* Transfer Type */

if(transferType){

    transferType.addEventListener(
        "change",
        function(){

            const isHttps =
            transferType.value ===
            "HTTPS";

            document.getElementById(
                "httpsSection"
            ).style.display =
            isHttps
            ? "block"
            : "none";

            document.getElementById(
                "sftpSection"
            ).style.display =
            isHttps
            ? "none"
            : "block";
        }
    );
}

/* File Validation */

fileInput.addEventListener(
    "change",
    function(){

        const file =
        this.files[0];

        if(!file){
            return;
        }

        if(
            !file.name
            .toLowerCase()
            .endsWith(".xml")
        ){

            alert(
                "Only XML files are allowed."
            );

            fileInput.value =
            "";

            selectedFile =
            null;

            return;
        }

        selectedFile =
        file;

        readXMLSummary(file);

        document.getElementById(
            "fileName"
        ).innerText =
        file.name;

        document.getElementById(
            "fileSize"
        ).innerText =
        (
            file.size / 1024
        ).toFixed(2)
        + " KB";

        document.getElementById(
            "fileType"
        ).innerText =
        "XML";
    }
);

/* Upload */

uploadButton.addEventListener(
    "click",
    uploadEPCIS
);

async function uploadEPCIS(){

    const start =
    performance.now();

    try{

        document.getElementById(
            "status"
        ).innerText =
        "Processing...";

        if(
            transferType.value ===
            "HTTPS"
        ){

            const selectedProfileId =
            Number(
                document.getElementById(
                    "profileSelect"
                ).value
            );

            const profiles =
            JSON.parse(
                localStorage.getItem(
                    "profiles"
                ) || "[]"
            );

            const profile =
            profiles.find(
                p => p.id === selectedProfileId
            );

            if(!profile){

                throw new Error(
                    "Please select a profile."
                );
            }

            /*
             * FIX: Validate that httpsUrl and apiToken
             * are present before sending the request.
             */

            if(!profile.httpsUrl){

                throw new Error(
                    "Selected profile is missing an HTTPS URL."
                );
            }

            if(!profile.apiToken){

                throw new Error(
                    "Selected profile is missing an API token."
                );
            }

            if(!selectedFile){

                throw new Error(
                    "Please select an XML file."
                );
            }

            const formData =
            new FormData();

            formData.append(
                "file",
                selectedFile
            );

            formData.append(
                "url",
                profile.httpsUrl
            );

            formData.append(
                "token",
                profile.apiToken
            );

            const response =
            await fetch(
                "/api/upload-epcis",
                {
                    method:"POST",
                    body:formData
                }
            );

            const result =
            await response.json();

            if(!response.ok){

                throw new Error(
                    result.details?.message
                    ||
                    result.error
                    ||
                    "Upload failed."
                );
            }

            document.getElementById(
                "status"
            ).innerHTML =
            '<span class="success">SUCCESS</span>';

            document.getElementById(
                "responseCode"
            ).innerText =
            response.status;

            document.getElementById(
                "responseMessage"
            ).innerText =
            JSON.stringify(
                result.data,
                null,
                2
            );
        }
        else{

            /*
             * SFTP branch
             */

            const selectedProfileId =
            Number(
                document.getElementById(
                    "sftpProfileSelect"
                ).value
            );

            const profiles =
            JSON.parse(
                localStorage.getItem(
                    "profiles"
                ) || "[]"
            );

            const profile =
            profiles.find(
                p => p.id === selectedProfileId
            );

            if(!profile){

                throw new Error(
                    "Please select a profile."
                );
            }

            if(!profile.host){

                throw new Error(
                    "Selected SFTP profile is missing a host."
                );
            }

            if(!profile.username){

                throw new Error(
                    "Selected SFTP profile is missing a username."
                );
            }

            if(!profile.password && !profile.privateKey){

                throw new Error(
                    "Selected SFTP profile needs a password or .pem SSH private key."
                );
            }

            if(!selectedFile){

                throw new Error(
                    "Please select an XML file."
                );
            }

            const sftpFormData =
            new FormData();

            sftpFormData.append(
                "file",
                selectedFile
            );

            sftpFormData.append(
                "host",
                profile.host
            );

            sftpFormData.append(
                "port",
                profile.port || "22"
            );

            sftpFormData.append(
                "username",
                profile.username
            );

            sftpFormData.append(
                "password",
                profile.password || ""
            );

            sftpFormData.append(
                "privateKey",
                profile.privateKey || ""
            );

            sftpFormData.append(
                "remotePath",
                profile.remotePath || ""
            );

            const sftpResponse =
            await fetch(
                "/api/upload-epcis-sftp",
                {
                    method: "POST",
                    body: sftpFormData
                }
            );

            const sftpResult =
            await sftpResponse.json();

            if(!sftpResponse.ok){

                throw new Error(
                    sftpResult.details?.message
                    ||
                    sftpResult.error
                    ||
                    "SFTP upload failed."
                );
            }

            document.getElementById(
                "status"
            ).innerHTML =
            '<span class="warning">FILE SUBMITTED</span>';

            document.getElementById(
                "responseCode"
            ).innerText =
            sftpResponse.status;

            document.getElementById(
                "responseMessage"
            ).innerText =
            sftpResult.data?.message
            ||
            "File submitted successfully via SFTP.";
        }

        /*
         * FIX: Duration is now correctly written after
         * both HTTPS and SFTP branches complete.
         * Previously the orphaned block below the else
         * caused a ReferenceError before reaching this.
         */

        const duration =
        (
            (
                performance.now()
                - start
            ) / 1000
        ).toFixed(2);

        document.getElementById(
            "duration"
        ).innerText =
        duration + " sec";

        incrementDashboardStat(
            "epcisUploads"
        );
    }
    catch(error){

        document.getElementById(
            "status"
        ).innerHTML =
        '<span class="error">FAILED</span>';

        document.getElementById(
            "responseMessage"
        ).innerText =
        error.message;
    }
}

function readXMLSummary(file){

    const reader =
    new FileReader();

    reader.onload =
    function(event){

        const xmlText =
        event.target.result;

        /*
         * FIX: Use DOMParser for accurate event counting
         * instead of regex on raw text. The old regex
         * matched the word "commission" anywhere —
         * including inside element names, attribute
         * values, and comments — inflating counts.
         *
         * We now count only top-level EPCIS event
         * elements by their bizStep or tag name.
         */

        let commissionCount = 0;
        let aggregationCount = 0;
        let destroyCount = 0;

        try{

            const parser =
            new DOMParser();

            const xmlDoc =
            parser.parseFromString(
                xmlText,
                "application/xml"
            );

            const parserError =
            xmlDoc.querySelector(
                "parsererror"
            );

            if(parserError){

                throw new Error(
                    "Invalid XML structure."
                );
            }

            /*
             * Commission: ObjectEvent with
             * bizStep containing "commissioning"
             */

            const objectEvents =
            Array.from(
                xmlDoc.getElementsByTagName(
                    "ObjectEvent"
                )
            );

            objectEvents.forEach(
                ev => {

                    const bizStep =
                    ev.getElementsByTagName(
                        "bizStep"
                    )[0];

                    if(
                        bizStep &&
                        bizStep.textContent
                        .toLowerCase()
                        .includes("commissioning")
                    ){
                        commissionCount++;
                    }
                }
            );

            /*
             * Aggregation: AggregationEvent elements
             */

            aggregationCount =
            xmlDoc.getElementsByTagName(
                "AggregationEvent"
            ).length;

            /*
             * Destroy: ObjectEvent with
             * bizStep containing "destroying"
             */

            objectEvents.forEach(
                ev => {

                    const bizStep =
                    ev.getElementsByTagName(
                        "bizStep"
                    )[0];

                    if(
                        bizStep &&
                        bizStep.textContent
                        .toLowerCase()
                        .includes("destroying")
                    ){
                        destroyCount++;
                    }
                }
            );
        }
        catch(err){

            /*
             * Fallback: if DOMParser fails (malformed XML),
             * fall back to conservative regex patterns.
             */

            const lowerXML =
            xmlText.toLowerCase();

            commissionCount =
            (
                lowerXML.match(
                    /urn:epcglobal:cbv:bizstep:commissioning/gi
                ) || []
            ).length;

            aggregationCount =
            (
                lowerXML.match(
                    /<aggregationevent[\s>]/gi
                ) || []
            ).length;

            destroyCount =
            (
                lowerXML.match(
                    /urn:epcglobal:cbv:bizstep:destroying/gi
                ) || []
            ).length;
        }

        const totalEvents =
        commissionCount +
        aggregationCount +
        destroyCount;

        document.getElementById(
            "commissionCount"
        ).innerText =
        commissionCount;

        document.getElementById(
            "aggregationCount"
        ).innerText =
        aggregationCount;

        document.getElementById(
            "destroyCount"
        ).innerText =
        destroyCount;

        document.getElementById(
            "totalCount"
        ).innerText =
        totalEvents;
    };

    reader.readAsText(file);
}

/* Clear */

clearButton.addEventListener(
    "click",
    clearForm
);

function clearForm(){

    selectedFile =
    null;

    fileInput.value =
    "";

    document.getElementById(
        "fileName"
    ).innerText =
    "-";

    document.getElementById(
        "fileSize"
    ).innerText =
    "-";

    document.getElementById(
        "fileType"
    ).innerText =
    "-";

    document.getElementById(
        "commissionCount"
    ).innerText =
    "-";

    document.getElementById(
        "aggregationCount"
    ).innerText =
    "-";

    document.getElementById(
        "destroyCount"
    ).innerText =
    "-";

    document.getElementById(
        "totalCount"
    ).innerText =
    "-";

    document.getElementById(
        "status"
    ).innerText =
    "Ready";

    document.getElementById(
        "duration"
    ).innerText =
    "-";

    document.getElementById(
        "responseCode"
    ).innerText =
    "-";

    document.getElementById(
        "responseMessage"
    ).innerText =
    "No response available.";
}

/*
 * FIX: Null-check transferType before dispatching
 * the change event, so a missing element doesn't
 * block loadProfiles() from running.
 */

if(transferType){

    transferType.dispatchEvent(
        new Event("change")
    );
}

loadProfiles();
