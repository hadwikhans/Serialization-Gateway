let serialNumbers = [];
const API_BASE =
'https://epcis-simulation-production.up.railway.app';

const serializationType =
document.getElementById("serializationType");

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

    profileSelect.innerHTML =
    `
    <option value="">
        Select Profile
    </option>
    `;

    profiles
    .filter(
        profile =>

        profile.module ===
        "REQUEST_SERIALS"

        &&

        profile.active
    )
    .forEach(
        profile => {

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
    );
}

serializationType.addEventListener(
"change",
updateSections
);

document
.getElementById("requestButton")
.addEventListener(
"click",
sendRequest
);

document
.getElementById("clearButton")
.addEventListener(
"click",
clearForm
);

document
.querySelectorAll("input,select")
.forEach(el => {

    el.addEventListener(
        "input",
        generatePayload
    );

    el.addEventListener(
        "change",
        generatePayload
    );

});

function updateSections(){

const type =
    serializationType.value;

if(type === "SSCC"){

    document.getElementById(
        "ssccSection"
    ).style.display = "block";

    document.getElementById(
        "gtinSection"
    ).style.display = "none";
}
else{

    document.getElementById(
        "ssccSection"
    ).style.display = "none";

    document.getElementById(
        "gtinSection"
    ).style.display = "block";
}

generatePayload();

}

function generatePayload(){

const type =
    serializationType.value;

const payload = {

    network_link:null,

    plant_sgln:
        document.getElementById(
            "plantSgln"
        ).value,

    po_number:null,

    po_line_number:null,

    work_order_number:null,

    reference_identifier:null,

    quantity:Number(
        document.getElementById(
            "quantity"
        ).value
    ),

    system_name:
        document.getElementById(
            "systemName"
        ).value
};

if(type === "GTIN"){

    payload.encoding_type =
        "AI(01)+AI(21)";

    payload.packaging_code =
        document.getElementById(
            "packagingCode"
        ).value;

    payload.gs1_company_prefix =
        null;

    payload.extension_digit =
        null;
}
else{

    payload.encoding_type =
        "AI(00)";

    payload.packaging_code =
        null;

    payload.gs1_company_prefix =
        document.getElementById(
            "gcp"
        ).value;

    payload.extension_digit =
        document.getElementById(
            "extensionDigit"
        ).value;
}

return payload;

}

function validateForm(){

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
    p =>
    p.id ===
    selectedProfileId
);

if(!profile){

    alert(
        "Please select a profile."
    );

    return false;
}

const token =
profile.apiToken;

const url =
profile.httpsUrl;

const quantity =
    Number(
        document.getElementById(
            "quantity"
        ).value
    );

if(!token){

    alert(
        "Token is required"
    );

    return false;
}

if(!url){

    alert(
        "Request URL is required"
    );

    return false;
}

if(quantity <= 0){

    alert(
        "Quantity must be greater than 0"
    );

    return false;
}

return true;

}

function normalizeSerialResponse(data){

    if(Array.isArray(data)){
        return data;
    }

    const possibleLists = [
        data?.serialNumbers,
        data?.serial_numbers,
        data?.serials,
        data?.data?.serialNumbers,
        data?.data?.serial_numbers,
        data?.data?.serials,
        data?.result?.serialNumbers,
        data?.result?.serial_numbers
    ];

    const list =
    possibleLists.find(
        item => Array.isArray(item)
    );

    if(list){
        return list;
    }

    return [];
}

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

async function sendRequest(){

if(!validateForm()){
    return;
}

const start =
    performance.now();

try{

    document
        .getElementById(
            "status"
        )
        .innerText =
        "Processing...";

    const payload =
        generatePayload();

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

    const token =
    profile.apiToken;

    const url =
    profile.httpsUrl;

    const response =
        await fetch('https://epcis-simulation-production.up.railway.app/api/request-serials')
            {
                method:"POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body:
                JSON.stringify({

                url:url,

                token:token,

                    payload:
                    payload
                })
            }
        );

    const data =
        await response.json();

    if(!response.ok){

        throw new Error(
            JSON.stringify(
                data,
                null,
                2
            )
        );
    }

    serialNumbers =
    normalizeSerialResponse(data);

    if(serialNumbers.length === 0){

        throw new Error(
            "Request succeeded, but no serial numbers were found in the response."
        );
    }

    document
        .getElementById(
            "firstSerial"
        )
        .innerText =
        serialNumbers[0] || "-";

    document
        .getElementById(
            "lastSerial"
        )
        .innerText =
        serialNumbers[
            serialNumbers.length - 1
        ] || "-";

    document
        .getElementById(
            "totalGenerated"
        )
        .innerText =
        serialNumbers.length;

    document
        .getElementById(
            "status"
        )
        .innerHTML =
        '<span class="success">SUCCESS</span>';

    document
        .getElementById(
            "requestedQty"
        )
        .innerText =
        payload.quantity;

    document
        .getElementById(
            "receivedQty"
        )
        .innerText =
        serialNumbers.length;

    const duration =
    (
        (
            performance.now()
            - start
        ) / 1000
    ).toFixed(2);

    document
        .getElementById(
            "duration"
        )
        .innerText =
        duration + " sec";

    document
        .getElementById(
            "errorSection"
        )
        .style.display =
        "none";

    incrementDashboardStat(
        "serialRequests"
    );

    document
        .getElementById(
            "errorMessage"
        )
        .innerText = "";

}
catch(error){

    document
        .getElementById(
            "status"
        )
        .innerHTML =
        '<span class="error">FAILED</span>';

    document
        .getElementById(
            "errorSection"
        )
        .style.display =
        "block";

    document
        .getElementById(
            "errorMessage"
        )
        .innerText =
        error.message;
}

}

function clearForm(){

document
    .getElementById(
        "profileSelect"
    )
    .value = "";

document
    .getElementById(
        "plantSgln"
    )
    .value = "";

document
    .getElementById(
        "systemName"
    )
    .value = "";

document
    .getElementById(
        "quantity"
    )
    .value = "1";

document
    .getElementById(
        "packagingCode"
    )
    .value = "";

document
    .getElementById(
        "gcp"
    )
    .value = "";

document
    .getElementById(
        "extensionDigit"
    )
    .value = "";

serialNumbers = [];

document
    .getElementById(
        "status"
    )
    .innerText = "Ready";

document
    .getElementById(
        "requestedQty"
    )
    .innerText = "0";

document
    .getElementById(
        "receivedQty"
    )
    .innerText = "0";

document
    .getElementById(
        "duration"
    )
    .innerText = "0 sec";

document
    .getElementById(
        "firstSerial"
    )
    .innerText = "-";

document
    .getElementById(
        "lastSerial"
    )
    .innerText = "-";

document
    .getElementById(
        "totalGenerated"
    )
    .innerText = "0";

document
    .getElementById(
        "errorSection"
    )
    .style.display =
    "none";

document
    .getElementById(
        "errorMessage"
    )
    .innerText = "";

generatePayload();

}

function getTimestamp(){

return new Date()
    .toISOString()
    .replace(/[:.]/g,'-');

}

function downloadCSV(){

if(serialNumbers.length === 0)
    return;

let csv =
    "Serial Numbers\n";

serialNumbers.forEach(
    serial => {

        csv +=
            serial + "\n";
    }
);

const blob =
    new Blob(
        [csv],
        {
            type:"text/csv"
        }
    );

const link =
    document.createElement(
        "a"
    );

link.href =
    URL.createObjectURL(
        blob
    );

link.download =
    `REQUISITION_${getTimestamp()}.csv`;

link.click();

}

function downloadJSON(){

if(serialNumbers.length === 0)
    return;

const blob =
    new Blob(
        [
            JSON.stringify(
                serialNumbers,
                null,
                2
            )
        ],
        {
            type:
            "application/json"
        }
    );

const link =
    document.createElement(
        "a"
    );

link.href =
    URL.createObjectURL(
        blob
    );

link.download =
    `REQUISITION_${getTimestamp()}.json`;

link.click();

}

function downloadXLSX(){

if(serialNumbers.length === 0)
    return;

const rows =
    serialNumbers.map(
        serial => ({
            "Serial Number":
            serial
        })
    );

const worksheet =
    XLSX.utils.json_to_sheet(
        rows
    );

const workbook =
    XLSX.utils.book_new();

XLSX.utils.book_append_sheet(
    workbook,
    worksheet,
    "Serial Numbers"
);

XLSX.writeFile(
    workbook,
    `REQUISITION_${getTimestamp()}.xlsx`
);

}

function copySerials(){

if(serialNumbers.length === 0)
    return;

navigator.clipboard.writeText(
    serialNumbers.join("\n")
);

alert(
    "Serial Numbers Copied"
);

}

/* Modal */

const viewAllLink =
document.getElementById(
    "viewAllLink"
);

const serialModal =
document.getElementById(
    "serialModal"
);

const closeModal =
document.getElementById(
    "closeModal"
);

viewAllLink.addEventListener(
    "click",
    function(e){

        e.preventDefault();

        const container =
            document.getElementById(
                "modalSerialList"
            );

        container.innerHTML =
            serialNumbers
            .map(
                serial =>
                `<div>${serial}</div>`
            )
            .join("");

        serialModal.style.display =
            "flex";
    }
);

closeModal.addEventListener(
    "click",
    function(){

        serialModal.style.display =
            "none";
    }
);

window.addEventListener(
    "click",
    function(event){

        if(
            event.target ===
            serialModal
        ){

            serialModal.style.display =
                "none";
        }

    }
);

loadProfiles();

updateSections();
