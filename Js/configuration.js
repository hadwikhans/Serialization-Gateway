/* Elements */

const connectionType =
document.getElementById(
    "connectionType"
);

const saveProfile =
document.getElementById(
    "saveProfile"
);

const clearProfile =
document.getElementById(
    "clearProfile"
);

const profileTableBody =
document.getElementById(
    "profileTableBody"
);

let editProfileId = null;
let selectedPrivateKey = "";
let selectedPrivateKeyName = "";

function getProfiles(){

    return JSON.parse(
        localStorage.getItem(
            "profiles"
        ) || "[]"
    );
}

function setProfiles(profiles){

    localStorage.setItem(
        "profiles",
        JSON.stringify(
            profiles
        )
    );
}

/* HTTPS / SFTP Toggle */

function updateSections(){

    const isHttps =
    connectionType.value ===
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

connectionType.addEventListener(
    "change",
    updateSections
);

document
.querySelectorAll(
    'input[name="moduleType"]'
)
.forEach(input => {

    input.addEventListener(
        "change",
        function(){

            if(
                this.value ===
                "REQUEST_SERIALS"
            ){

                connectionType.value =
                "HTTPS";
            }

            updateSections();
        }
    );
});

document
.getElementById(
    "privateKey"
)
.addEventListener(
    "change",
    function(){

        const file =
        this.files[0];

        selectedPrivateKey =
        "";

        selectedPrivateKeyName =
        "";

        document.getElementById(
            "privateKeyName"
        ).innerText =
        "";

        if(!file){
            return;
        }

        if(
            !file.name
            .toLowerCase()
            .endsWith(".pem")
        ){

            alert(
                "SSH private key must be a .pem file."
            );

            this.value =
            "";

            return;
        }

        const reader =
        new FileReader();

        reader.onload =
        function(event){

            selectedPrivateKey =
            event.target.result;

            selectedPrivateKeyName =
            file.name;

            document.getElementById(
                "privateKeyName"
            ).innerText =
            file.name;
        };

        reader.readAsText(file);
    }
);

/* Save Profile */

saveProfile.addEventListener(
    "click",
    saveConfiguration
);

function saveConfiguration(){

    const profiles =
    getProfiles();

    const moduleType =
    document.querySelector(
        'input[name="moduleType"]:checked'
    ).value;

    const profile = {

        id:
        Date.now(),

        active:
        true,

        module:
        moduleType,

        connectionType:
        connectionType.value,

        profileName:
        document.getElementById(
            "profileName"
        ).value,

        environment:
        document.getElementById(
            "environment"
        ).value,

        httpsUrl:
        document.getElementById(
            "httpsUrl"
        )?.value || "",

        apiToken:
        document.getElementById(
            "apiToken"
        )?.value || "",

        host:
        document.getElementById(
            "host"
        )?.value || "",

        port:
        document.getElementById(
            "port"
        )?.value || "",

        username:
        document.getElementById(
            "username"
        )?.value || "",

        password:
        document.getElementById(
            "password"
        )?.value || "",

        privateKey:
        selectedPrivateKey,

        privateKeyName:
        selectedPrivateKeyName,

        remotePath:
        document.getElementById(
            "remotePath"
        )?.value || ""

    };

    if(
        !profile.profileName
    ){

        alert(
            "Profile Name is required."
        );

        return;
    }

    if(
        profile.module ===
        "REQUEST_SERIALS"
        &&
        profile.connectionType !==
        "HTTPS"
    ){

        alert(
            "Request Serials profiles must use HTTPS."
        );

        return;
    }

    if(profile.connectionType === "HTTPS"){

        if(!profile.httpsUrl){

            alert(
                "HTTPS URL is required."
            );

            return;
        }

        if(!profile.apiToken){

            alert(
                "API Token is required."
            );

            return;
        }
    }
    else{

        if(!profile.host){

            alert(
                "SFTP Hostname is required."
            );

            return;
        }

        if(!profile.username){

            alert(
                "SFTP Username is required."
            );

            return;
        }

        if(
            !profile.password
            &&
            !profile.privateKey
        ){

            alert(
                "SFTP Password or .pem SSH Private Key is required."
            );

            return;
        }
    }

    if(editProfileId){

        const index =
        profiles.findIndex(
            p => p.id === editProfileId
        );

        if(index === -1){

            alert(
                "Profile not found."
            );

            editProfileId = null;

            return;
        }

        profile.id =
        editProfileId;

        profile.active =
        profiles[index].active;

        if(
            profile.connectionType === "SFTP"
            &&
            !profile.privateKey
        ){

            profile.privateKey =
            profiles[index].privateKey || "";

            profile.privateKeyName =
            profiles[index].privateKeyName || "";
        }

        profiles[index] =
        profile;

        editProfileId = null;
    }
    else{

        profiles.push(
            profile
        );
    }

    setProfiles(profiles);

    loadProfiles();

    clearForm();

    alert(
        "Profile Saved Successfully."
    );
}

/* Load Profiles */

function loadProfiles(){

    const profiles =
    getProfiles();

    profileTableBody.innerHTML =
    "";

    document.getElementById(
        "totalProfiles"
    ).innerText =
    profiles.length;

    document.getElementById(
        "activeProfiles"
    ).innerText =
    profiles.filter(
        profile => profile.active
    ).length;

    document.getElementById(
        "httpsProfiles"
    ).innerText =
    profiles.filter(
        profile =>
        profile.connectionType === "HTTPS"
    ).length;

    document.getElementById(
        "sftpProfiles"
    ).innerText =
    profiles.filter(
        profile =>
        profile.connectionType === "SFTP"
    ).length;

    profiles.forEach(
        profile => {

            const row =
            document.createElement(
                "tr"
            );

            row.innerHTML =

            `
            <td>
                ${profile.profileName}
            </td>

            <td>
                ${profile.module}
            </td>

            <td>
                ${profile.connectionType}
            </td>

            <td>
                ${profile.environment}
            </td>

            <td>
                ${
                    profile.active
                    ? "🟢 Active"
                    : "🔴 Inactive"
                }
            </td>

            <td>

                <div class="action-buttons">

                    <button onclick="toggleProfile(${profile.id})">

                        ${
                            profile.active
                            ? "Deactivate"
                            : "Activate"
                        }

                    </button>

                    <button onclick="editProfile(${profile.id})">

                        Edit

                    </button>

                    <button onclick="deleteProfile(${profile.id})">

                        Delete

                    </button>

                </div>

            </td>
            `;

            profileTableBody.appendChild(
                row
            );
        }
    );
}

/* Activate / Deactivate */

window.toggleProfile =
function(id){

    const profiles =
    getProfiles();

    const profile =
    profiles.find(
        p => p.id === id
    );

    if(profile){

        profile.active =
        !profile.active;
    }

    setProfiles(profiles);

    loadProfiles();
};

/* Delete */

window.deleteProfile =
function(id){

    if(
        !confirm(
            "Delete profile?"
        )
    ){
        return;
    }

    const profiles =
    getProfiles();

    const updatedProfiles =
    profiles.filter(
        p => p.id !== id
    );

    setProfiles(updatedProfiles);

    loadProfiles();
};

/* Edit */

window.editProfile =
function(id){

    const profiles =
    getProfiles();

    const profile =
    profiles.find(
        p => p.id === id
    );

    if(!profile){
        return;
    }

    editProfileId = id;

    document.getElementById(
        "profileName"
    ).value =
    profile.profileName;

    document.getElementById(
        "environment"
    ).value =
    profile.environment;

    connectionType.value =
    profile.connectionType;

    updateSections();

    if(profile.connectionType === "HTTPS"){

        document.getElementById(
            "httpsUrl"
        ).value =
        profile.httpsUrl || "";

        document.getElementById(
            "apiToken"
        ).value =
        profile.apiToken || "";
    }
    else{

        document.getElementById(
            "host"
        ).value =
        profile.host || "";

        document.getElementById(
            "port"
        ).value =
        profile.port || "22";

        document.getElementById(
            "username"
        ).value =
        profile.username || "";

        document.getElementById(
            "password"
        ).value =
        profile.password || "";

        selectedPrivateKey =
        profile.privateKey || "";

        selectedPrivateKeyName =
        profile.privateKeyName || "";

        document.getElementById(
            "privateKeyName"
        ).innerText =
        selectedPrivateKeyName
        ? `Current key: ${selectedPrivateKeyName}`
        : "";

        document.getElementById(
            "remotePath"
        ).value =
        profile.remotePath || "";
    }

    document.querySelector(
        `input[name="moduleType"][value="${profile.module}"]`
    ).checked = true;

    saveProfile.innerText =
    "UPDATE PROFILE";
};

/* Clear */

clearProfile.addEventListener(
    "click",
    clearForm
);

function clearForm(){

    document.getElementById(
        "profileName"
    ).value = "";

    document.getElementById(
        "httpsUrl"
    ).value = "";

    document.getElementById(
        "apiToken"
    ).value = "";

    document.getElementById(
        "host"
    ).value = "";

    document.getElementById(
        "port"
    ).value = "22";

    document.getElementById(
        "username"
    ).value = "";

    document.getElementById(
        "password"
    ).value = "";

    document.getElementById(
        "privateKey"
    ).value = "";

    document.getElementById(
        "privateKeyName"
    ).innerText = "";

    selectedPrivateKey =
    "";

    selectedPrivateKeyName =
    "";

    document.getElementById(
        "remotePath"
    ).value = "";

    saveProfile.innerText =
        "SAVE PROFILE";

        editProfileId = null;

}

/* Initialize */

updateSections();

loadProfiles();
