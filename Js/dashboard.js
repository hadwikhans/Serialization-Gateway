function getStoredArray(key){

    try{

        const value =
        JSON.parse(
            localStorage.getItem(key) || "[]"
        );

        return Array.isArray(value)
        ? value
        : [];
    }
    catch(error){

        return [];
    }
}

function getStoredStats(){

    try{

        return JSON.parse(
            localStorage.getItem("dashboardStats") || "{}"
        );
    }
    catch(error){

        return {};
    }
}

function updateDashboardCounts(){

    const profiles =
    getStoredArray("profiles");

    const stats =
    getStoredStats();

    document.getElementById(
        "activeProfilesCount"
    ).innerText =
    profiles.filter(
        profile => profile.active
    ).length;

    document.getElementById(
        "serialRequestsCount"
    ).innerText =
    stats.serialRequests || 0;

    document.getElementById(
        "epcisUploadsCount"
    ).innerText =
    stats.epcisUploads || 0;

    document.getElementById(
        "generatedFilesCount"
    ).innerText =
    stats.generatedFiles || 0;
}

updateDashboardCounts();
