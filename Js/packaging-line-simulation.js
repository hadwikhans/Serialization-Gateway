let currentStep = 1;

const totalSteps = 7;

const levelOrder = [
    "EACH",
    "INNERPACK",
    "CASE",
    "PALLET"
];

const levelConfig = {
    EACH: {
        key: "each",
        uom: "EA",
        type: "sgtin"
    },
    INNERPACK: {
        key: "inner",
        uom: "BU",
        type: "sscc"
    },
    CASE: {
        key: "case",
        uom: "CA",
        type: "sscc"
    },
    PALLET: {
        key: "pallet",
        uom: "PA",
        type: "sscc"
    }
};

const simulationData = {
    product: {},
    packagingLevels: ["EACH"],
    hierarchy: {},
    files: {
        serialFiles: {},
        serialNumbersByLevel: {},
        fileName: "epcis-events.xml",
        outputFormat: "XML"
    },
    events: [],
    schema: {},
    generated: {
        serialsByLevel: {},
        eventCount: 0
    }
};

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

function escapeXml(value){

    return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function padSerial(number, length){

    return String(number)
    .padStart(length, "0");
}

function getNowIso(){

    return new Date()
    .toISOString()
    .replace(/\.\d{3}Z$/, "Z");
}

function getOffset(){

    const offsetMinutes =
    -new Date().getTimezoneOffset();

    const sign =
    offsetMinutes >= 0 ? "+" : "-";

    const absolute =
    Math.abs(offsetMinutes);

    const hours =
    padSerial(Math.floor(absolute / 60), 2);

    const minutes =
    padSerial(absolute % 60, 2);

    return `${sign}${hours}:${minutes}`;
}

function getProfiles(){

    return JSON.parse(
        localStorage.getItem(
            "profiles"
        ) || "[]"
    );
}

function setSerialFileStatus(level, message, isError = false){

    const status =
    document.getElementById(
        `serialStatus-${level}`
    );

    if(!status){
        return;
    }

    status.textContent = message || "";
    status.style.color =
    isError ? "#d9534f" : "#2d6a4f";
}

function extractSerialsFromRecords(records){

    if(!Array.isArray(records)){
        return [];
    }

    const headerKeys = [
        "serial numbers",
        "serial number"
    ];

    const values = [];

    records.forEach(record => {

        if(typeof record === "string"){
            values.push(record.trim());
            return;
        }

        if(record && typeof record === "object"){

            const key = Object.keys(record)
            .find(k =>
                headerKeys.includes(
                    k.trim().toLowerCase()
                )
            );

            if(key){
                values.push(
                    String(record[key] || "").trim()
                );
            }
        }
    });

    return values
    .filter(value => value !== "");
}

function parseCsvText(text){

    const rows = text
    .trim()
    .split(/\r?\n/)
    .filter(line => line.trim() !== "");

    if(rows.length === 0){
        return [];
    }

    const parseRow = row => {
        return row
        .match(/("(?:[^"]|"")*"|[^,]*)(?:,|$)/g)
        .map(cell =>
            cell
            .replace(/^"|"$/g, "")
            .replace(/""/g, '"')
            .trim()
        )
        .filter((_, index, arr) => index < arr.length);
    };

    const headers = parseRow(rows[0]);
    const headerName = headers
    .find(h =>
        ["serial numbers","serial number"].includes(
            h.trim().toLowerCase()
        )
    );

    if(!headerName){
        return [];
    }

    const headerIndex = headers.indexOf(headerName);
    const values = [];

    for(let i = 1; i < rows.length; i++){
        const cols = parseRow(rows[i]);
        if(cols[headerIndex]){
            values.push(cols[headerIndex]);
        }
    }

    return values.filter(Boolean);
}

function parseSerialFile(file){

    return new Promise((resolve, reject) => {

        const reader = new FileReader();
        const extension =
        file.name
        .split(".")
        .pop()
        .toLowerCase();

        reader.onload = event => {

            try {

                const content = event.target.result;
                let serials = [];

                if(extension === "csv"){
                    serials = parseCsvText(content);
                }
                else if(extension === "json"){

                    const data = JSON.parse(content);

                    if(Array.isArray(data)){
                        serials = extractSerialsFromRecords(data);
                    }
                    else if(data && typeof data === "object"){

                        const candidate =
                        data.serialNumbers
                        || data.serialNumber
                        || data["Serial Numbers"]
                        || data["Serial Number"];

                        if(Array.isArray(candidate)){
                            serials = extractSerialsFromRecords(candidate);
                        }
                        else if(typeof candidate === "string"){
                            serials = candidate
                            .split(/\r?\n/)
                            .map(item => item.trim())
                            .filter(Boolean);
                        }
                    }
                }
                else if(extension === "xlsx"){

                    if(typeof XLSX === "undefined"){
                        throw new Error(
                            "XLSX parser not available."
                        );
                    }

                    const workbook = XLSX.read(content, {
                        type: "binary"
                    });

                    const sheetName = workbook.SheetNames[0];
                    const sheet = workbook.Sheets[sheetName];
                    const rows = XLSX.utils.sheet_to_json(sheet, {
                        defval: ""
                    });

                    serials = extractSerialsFromRecords(rows);
                }
                else {
                    throw new Error(
                        "Unsupported serial number file type."
                    );
                }

                if(serials.length === 0){
                    throw new Error(
                        "No serial numbers found. Use header 'Serial Numbers' or 'Serial Number'."
                    );
                }

                resolve(serials);
            }
            catch(error){
                reject(error);
            }
        };

        reader.onerror = () =>
        reject(new Error(
            "Unable to read serial number file."
        ));

        if(extension === "xlsx"){
            reader.readAsBinaryString(file);
        }
        else {
            reader.readAsText(file);
        }
    });
}

async function parseAllSerialFiles(){

    const labels = {
        EACH: "Eaches",
        INNERPACK: "Inner Packs",
        CASE: "Cases",
        PALLET: "Pallets"
    };

    const levels = getSelectedLevels();

    simulationData.files.serialNumbersByLevel = {};

    for(const level of levels){

        const file = simulationData.files.serialFiles[level];

        if(!file){
            throw new Error(
                `Select a serial number file for ${labels[level] || level}.`
            );
        }

        setSerialFileStatus(
            level,
            `Parsing ${file.name}...`
        );

        const serials = await parseSerialFile(file);

        simulationData.files.serialNumbersByLevel[level] = serials;
        setSerialFileStatus(
            level,
            `Loaded ${serials.length} serial numbers from ${file.name}.`
        );
    }
}

function buildSerialFileInputs(){

    const container =
    document.getElementById(
        "serialFileInputsContainer"
    );

    if(!container){
        return;
    }

    container.innerHTML = "";

    const levels =
    getSelectedLevels();

    if(levels.length === 0){
        container.innerHTML =
        `<p>
            Select packaging levels first.
        </p>`;
        return;
    }

    const labels = {
        EACH: "Eaches",
        INNERPACK: "Inner Packs",
        CASE: "Cases",
        PALLET: "Pallets"
    };

    levels.forEach(level => {

        const group =
        document.createElement("div");
        group.className = "form-group";

        const fileId =
        `serialFileInput-${level}`;

        group.innerHTML =
        `
            <label>
                ${labels[level] || level} Serial Number File
            </label>
            <input
                type="file"
                id="${fileId}"
                accept=".json,.csv,.xlsx">
            <p id="serialStatus-${level}" class="field-help"></p>
        `;

        container.appendChild(group);

        const input =
        group.querySelector("input");

        input.addEventListener(
            "change",
            event => {

                const file = event.target.files[0];

                if(!file){
                    delete simulationData.files.serialFiles[level];
                    setSerialFileStatus(level, "No file selected.");
                    return;
                }

                simulationData.files.serialFiles[level] = file;
                setSerialFileStatus(
                    level,
                    `Selected ${file.name}`
                );
            }
        );
    });
}

function loadSchemaProfiles(){

    const select =
    document.getElementById(
        "schemaProfileSelect"
    );

    if(!select){
        return;
    }

    select.innerHTML =
    `
    <option value="">
        Select Profile
    </option>
    `;

    getProfiles()
    .filter(
        profile =>
        profile.module === "EPCIS_SAMPLE_SCHEMA"
        &&
        profile.active
    )
    .forEach(profile => {

        const option =
        document.createElement(
            "option"
        );

        option.value =
        profile.id;

        option.textContent =
        `${profile.profileName} (${profile.connectionType})`;

        select.appendChild(
            option
        );
    });
}

function showStep(step){

    document
    .querySelectorAll('[id^="step"]')
    .forEach(section => {
        section.style.display = "none";
    });

    const activeStep =
    document.getElementById(
        "step" + step
    );

    if(activeStep){
        activeStep.style.display =
        "block";
    }

    document
    .querySelectorAll(
        ".wizard-step"
    )
    .forEach(
        (item,index) => {
            item.classList.toggle(
                "active",
                index + 1 === step
            );
        }
    );

    document.getElementById(
        "previousStep"
    ).disabled =
    step === 1;

    document.getElementById(
        "nextStep"
    ).style.display =
    step === totalSteps
    ? "none"
    : "inline-block";

    if(step === 4){
        buildSerialFileInputs();
    }

    if(step === 6){
        loadSchemaProfiles();
        if(!document.getElementById("sampleSchema").value.trim()){
            document.getElementById("sampleSchema").value =
            buildSampleSchema();
        }
    }

    if(step === totalSteps){
        renderSummary();
    }
}

function collectProduct(){

    simulationData.product = {
        lotNumber:
        document.getElementById(
            "lotNumber"
        ).value.trim(),

        materialNumber:
        document.getElementById(
            "materialNumber"
        ).value.trim(),

        eachQuantity:
        Math.max(
            1,
            Number(
                document.getElementById(
                    "eachQuantity"
                ).value
            ) || 1
        ),

        gcp:
        document.getElementById(
            "gcp"
        ).value.trim(),

        extensionDigit:
        document.getElementById(
            "extensionDigit"
        ).value || "0",

        internalMaterialCode:
        document.getElementById(
            "internalMaterialCode"
        ).value.trim(),

        senderSgln:
        document.getElementById(
            "senderSgln"
        ).value.trim(),

        receiverSgln:
        document.getElementById(
            "receiverSgln"
        ).value.trim(),

        manufacturingDate:
        document.getElementById(
            "manufacturingDate"
        ).value,

        expirationDate:
        document.getElementById(
            "expirationDate"
        ).value
    };
}

function getSelectedLevels(){

    return levelOrder.filter(
        level =>
        simulationData.packagingLevels.includes(
            level
        )
    );
}

function buildHierarchy(){

    const container =
    document.getElementById(
        "hierarchyBuilder"
    );

    container.innerHTML = "";

    const levels =
    getSelectedLevels();

    if(levels.length < 2){

        container.innerHTML =
        `
        <p>
            Select at least two packaging levels for aggregation.
        </p>
        `;

        return;
    }

    for(let i = 0; i < levels.length - 1; i++){

        const group =
        document.createElement(
            "div"
        );

        group.className =
        "form-group";

        group.innerHTML =
        `
        <label>
            ${levels[i]} PER ${levels[i + 1]}
        </label>
        <input
            data-child-level="${levels[i]}"
            data-parent-level="${levels[i + 1]}"
            type="number"
            min="1"
            value="${simulationData.hierarchy[`${levels[i]}_PER_${levels[i + 1]}`] || 1}"
            placeholder="Enter Quantity">
        `;

        container.appendChild(
            group
        );
    }
}

function collectHierarchy(){

    simulationData.hierarchy = {};

    document
    .querySelectorAll(
        "#hierarchyBuilder input"
    )
    .forEach(input => {

        const key =
        `${input.dataset.childLevel}_PER_${input.dataset.parentLevel}`;

        simulationData.hierarchy[key] =
        Math.max(
            1,
            Number(input.value) || 1
        );
    });
}

function collectFileOptions(){

    simulationData.files.fileName =
    simulationData.files.fileName ||
    "epcis-events.xml";

    simulationData.files.outputFormat =
    simulationData.files.outputFormat || "XML";
}

function collectEvents(){

    simulationData.events = [];

    if(document.getElementById("eventCommission").checked){
        simulationData.events.push("Commission");
    }

    if(document.getElementById("eventAggregation").checked){
        simulationData.events.push("Aggregation");
    }

    if(document.getElementById("eventDestroy").checked){
        simulationData.events.push("Destroy");
    }
}

function collectSchema(){

    const selectedProfileId =
    Number(
        document.getElementById(
            "schemaProfileSelect"
        ).value
    );

    const profile =
    getProfiles()
    .find(
        item => item.id === selectedProfileId
    );

    simulationData.schema = {
        epcisVersion:
        document.getElementById(
            "epcisVersion"
        ).value,

        bizLocation:
        document.getElementById(
            "bizLocation"
        ).value.trim(),

        profileId:
        selectedProfileId || null,

        profileName:
        profile?.profileName || "",

        sampleSchema:
        document.getElementById(
            "sampleSchema"
        ).value
    };
}

function collectCurrentStep(){

    if(currentStep === 1){
        collectProduct();
    }

    if(currentStep === 3){
        collectHierarchy();
    }

    if(currentStep === 4){
        collectFileOptions();
    }

    if(currentStep === 5){
        collectEvents();
    }

    if(currentStep === 6){
        collectSchema();
    }
}

function buildCountsByLevel(){

    const levels =
    getSelectedLevels();

    const counts = {};

    if(levels.length === 0){
        return counts;
    }

    counts[levels[0]] =
    simulationData.product.eachQuantity || 1;

    for(let i = 1; i < levels.length; i++){

        const childLevel =
        levels[i - 1];

        const parentLevel =
        levels[i];

        const packSize =
        simulationData.hierarchy[
            `${childLevel}_PER_${parentLevel}`
        ] || 1;

        counts[parentLevel] =
        Math.ceil(
            counts[childLevel] / packSize
        );
    }

    return counts;
}

function buildSerialsByLevel(){

    const product =
    simulationData.product;

    const counts =
    buildCountsByLevel();

    const serialsByLevel = {};

    const gcp =
    product.gcp || "0614141";

    const material =
    (product.materialNumber || "000001")
    .replace(/\W/g, "");

    Object.keys(counts)
    .forEach(level => {

        const uploadedSerials =
        simulationData.files.serialNumbersByLevel[level] || [];

        if(uploadedSerials.length > 0){
            serialsByLevel[level] = uploadedSerials.slice();
            return;
        }

        serialsByLevel[level] = [];

        for(let index = 1; index <= counts[level]; index++){

            if(levelConfig[level].type === "sgtin"){

                serialsByLevel[level].push(
                    `urn:epc:id:sgtin:${gcp}.${material}.${padSerial(index, 6)}`
                );
            }
            else{

                serialsByLevel[level].push(
                    `urn:epc:id:sscc:${gcp}.${product.extensionDigit || "0"}${padSerial(index, 16)}`
                );
            }
        }
    });

    return serialsByLevel;
}

function eventEnvelope(tagName, body){

    const eventTime =
    getNowIso();

    const location =
    simulationData.schema.bizLocation
    || simulationData.product.senderSgln
    || "0614141.00002.1";

    return `
            <${tagName}>
                <eventTime>${eventTime}</eventTime>
                <recordTime>${eventTime}</recordTime>
                <eventTimeZoneOffset>${getOffset()}</eventTimeZoneOffset>
${body}
                <readPoint>
                    <id>urn:epc:id:sgln:${escapeXml(location)}</id>
                </readPoint>
                <bizLocation>
                    <id>urn:epc:id:sgln:${escapeXml(location)}</id>
                </bizLocation>
            </${tagName}>`;
}

function buildObjectEvent(level, epcs, action, bizStep, disposition){

    const product =
    simulationData.product;

    const epcXml =
    epcs
    .map(epc => `                    <epc>${escapeXml(epc)}</epc>`)
    .join("\n");

    const ilmd =
    `
                <extension>
                    <ilmd>
                        <cbvmd:lotNumber>${escapeXml(product.lotNumber || "LOT001")}</cbvmd:lotNumber>
                        <cbvmd:manufacturingDate>${escapeXml(product.manufacturingDate || new Date().toISOString().slice(0, 10))}</cbvmd:manufacturingDate>
                        <cbvmd:itemExpirationDate>${escapeXml(product.expirationDate || new Date().toISOString().slice(0, 10))}</cbvmd:itemExpirationDate>
                        <ah:internalMaterialCode>${escapeXml(product.internalMaterialCode || product.materialNumber || "INT0001")}</ah:internalMaterialCode>
                        <ah:packagingUom>${escapeXml(levelConfig[level].uom)}</ah:packagingUom>
                    </ilmd>
                </extension>`;

    return eventEnvelope(
        "ObjectEvent",
        `
                <epcList>
${epcXml}
                </epcList>
                <action>${action}</action>
                <bizStep>urn:epcglobal:cbv:bizstep:${bizStep}</bizStep>
                <disposition>urn:epcglobal:cbv:disp:${disposition}</disposition>${ilmd}`
    );
}

function buildAggregationEvent(parentId, childEpcs){

    const childXml =
    childEpcs
    .map(epc => `                    <epc>${escapeXml(epc)}</epc>`)
    .join("\n");

    return eventEnvelope(
        "AggregationEvent",
        `
                <parentID>${escapeXml(parentId)}</parentID>
                <childEPCs>
${childXml}
                </childEPCs>
                <action>ADD</action>
                <bizStep>urn:epcglobal:cbv:bizstep:packing</bizStep>
                <disposition>urn:epcglobal:cbv:disp:in_progress</disposition>`
    );
}

function buildEpcisXml(){

    collectProduct();
    collectHierarchy();
    collectFileOptions();
    collectEvents();
    collectSchema();

    const serialsByLevel =
    buildSerialsByLevel();

    const events = [];

    if(simulationData.events.includes("Commission")){

        getSelectedLevels()
        .forEach(level => {

            const serials =
            serialsByLevel[level] || [];

            serials.forEach(serial => {
                events.push(
                    buildObjectEvent(
                        level,
                        [serial],
                        "ADD",
                        "commissioning",
                        "active"
                    )
                );
            });
        });
    }

    if(simulationData.events.includes("Aggregation")){

        const levels =
        getSelectedLevels();

        for(let i = 1; i < levels.length; i++){

            const childLevel =
            levels[i - 1];

            const parentLevel =
            levels[i];

            const packSize =
            simulationData.hierarchy[
                `${childLevel}_PER_${parentLevel}`
            ] || 1;

            const parents =
            serialsByLevel[parentLevel] || [];

            const children =
            serialsByLevel[childLevel] || [];

            parents.forEach((parentId, index) => {

                const childGroup =
                children.slice(
                    index * packSize,
                    index * packSize + packSize
                );

                if(childGroup.length > 0){
                    events.push(
                        buildAggregationEvent(
                            parentId,
                            childGroup
                        )
                    );
                }
            });
        }
    }

    if(simulationData.events.includes("Destroy")){

        const eachSerials =
        serialsByLevel.EACH || [];

        if(eachSerials.length > 0){
            events.push(
                buildObjectEvent(
                    "EACH",
                    eachSerials,
                    "DELETE",
                    "destroying",
                    "destroyed"
                )
            );
        }
    }

    simulationData.generated = {
        serialsByLevel,
        eventCount: events.length
    };

    const product =
    simulationData.product;

    return `<?xml version="1.0" encoding="UTF-8"?>
<epcis:EPCISDocument
    xmlns:epcis="urn:epcglobal:epcis:xsd:1"
    xmlns:ah="http://www.altiushub.com/epcis"
    xmlns:cbvmd="urn:epcglobal:cbv:mda"
    schemaVersion="${escapeXml(simulationData.schema.epcisVersion || "1.2")}"
    creationDate="${getNowIso()}">
    <EPCISHeader>
        <StandardBusinessDocumentHeader>
            <HeaderVersion>1.0</HeaderVersion>
            <Sender>
                <Identifier Authority="SGLN">${escapeXml(product.senderSgln || "0614141.00002.1")}</Identifier>
            </Sender>
            <Receiver>
                <Identifier Authority="SGLN">${escapeXml(product.receiverSgln || "0614141.00001.0")}</Identifier>
            </Receiver>
        </StandardBusinessDocumentHeader>
    </EPCISHeader>
    <EPCISBody>
        <EventList>
${events.join("\n")}
        </EventList>
    </EPCISBody>
</epcis:EPCISDocument>
`;
}

function buildSampleSchema(){

    return `<?xml version="1.0" encoding="UTF-8"?>
<epcis:EPCISDocument
    xmlns:epcis="urn:epcglobal:epcis:xsd:1"
    xmlns:ah="http://www.altiushub.com/epcis"
    xmlns:cbvmd="urn:epcglobal:cbv:mda"
    schemaVersion="1.2"
    creationDate="2026-06-09T00:00:00Z">
    <EPCISHeader>
        <StandardBusinessDocumentHeader>
            <Sender>
                <Identifier Authority="SGLN">sender_sgln</Identifier>
            </Sender>
            <Receiver>
                <Identifier Authority="SGLN">receiver_sgln</Identifier>
            </Receiver>
        </StandardBusinessDocumentHeader>
    </EPCISHeader>
    <EPCISBody>
        <EventList>
            <ObjectEvent>
                <eventTime>event_time</eventTime>
                <epcList>
                    <epc>commissioned_epc</epc>
                </epcList>
                <action>ADD</action>
                <bizStep>urn:epcglobal:cbv:bizstep:commissioning</bizStep>
                <disposition>urn:epcglobal:cbv:disp:active</disposition>
            </ObjectEvent>
            <AggregationEvent>
                <parentID>parent_epc</parentID>
                <childEPCs>
                    <epc>child_epc</epc>
                </childEPCs>
                <action>ADD</action>
                <bizStep>urn:epcglobal:cbv:bizstep:packing</bizStep>
                <disposition>urn:epcglobal:cbv:disp:in_progress</disposition>
            </AggregationEvent>
        </EventList>
    </EPCISBody>
</epcis:EPCISDocument>`;
}

function loadSampleSchema(){

    collectSchema();

    const profileLabel =
    simulationData.schema.profileName
    ? `\n<!-- Loaded using profile: ${escapeXml(simulationData.schema.profileName)} -->`
    : "";

    document.getElementById(
        "sampleSchema"
    ).value =
    buildSampleSchema() + profileLabel;
}

function renderSummary(){

    collectProduct();
    collectHierarchy();
    collectFileOptions();
    collectEvents();
    collectSchema();

    const counts =
    buildCountsByLevel();

    const uploadedSerialSummary =
    Object.entries(
        simulationData.files.serialNumbersByLevel || {}
    ).map(
        ([level, values]) =>
            `${level}: ${values.length}`
    ).join(", ");

    document.getElementById(
        "simulationSummary"
    ).innerHTML =
    `
        <p>Material : <span>${simulationData.product.materialNumber || "-"}</span></p>
        <p>Lot : <span>${simulationData.product.lotNumber || "-"}</span></p>
        <p>Levels : <span>${getSelectedLevels().join(" > ")}</span></p>
        <p>Quantities : <span>${Object.entries(counts).map(([key,value]) => `${key}: ${value}`).join(", ") || "-"}</span></p>
        <p>Serial files : <span>${uploadedSerialSummary || "None"}</span></p>
        <p>Events : <span>${simulationData.events.join(", ") || "-"}</span></p>
        <p>Schema Profile : <span>${simulationData.schema.profileName || "Default sample schema"}</span></p>
    `;
}

function normalizeFileName(fileName, format){

    const extension =
    format === "XML"
    ? ".xml"
    : ".json";

    return fileName
    .replace(/\.(xml|json)$/i, "")
    + extension;
}

async function generateSimulationFile(){

    try {
        await parseAllSerialFiles();
    }
    catch(error){
        alert(error.message || "Serial number file parsing failed.");
        return;
    }

    const xml =
    buildEpcisXml();

    const output =
    simulationData.files.outputFormat === "JSON"
    ? JSON.stringify(
        {
            input: simulationData,
            epcisXml: xml
        },
        null,
        2
    )
    : xml;

    document.getElementById(
        "generatedOutput"
    ).textContent =
    output;

    renderSummary();

    const blob =
    new Blob(
        [output],
        {
            type:
            simulationData.files.outputFormat === "JSON"
            ? "application/json"
            : "application/xml"
        }
    );

    const link =
    document.createElement(
        "a"
    );

    link.href =
    URL.createObjectURL(blob);

    link.download =
    normalizeFileName(
        simulationData.files.fileName,
        simulationData.files.outputFormat
    );

    link.click();

    URL.revokeObjectURL(
        link.href
    );

    incrementDashboardStat(
        "generatedFiles"
    );
}

document
.querySelectorAll(".level-card")
.forEach(card => {

    card.addEventListener(
        "click",
        function(){

            const level =
            this.dataset.level;

            this.classList.toggle(
                "selected"
            );

            if(this.classList.contains("selected")){

                if(!simulationData.packagingLevels.includes(level)){
                    simulationData.packagingLevels.push(level);
                }
            }
            else{

                simulationData.packagingLevels =
                simulationData.packagingLevels.filter(
                    item => item !== level
                );
            }

            simulationData.packagingLevels =
            getSelectedLevels();

            buildHierarchy();
        }
    );
});

document
.getElementById(
    "nextStep"
)
.addEventListener(
    "click",
    () => {

        collectCurrentStep();

        if(currentStep === 2){
            buildHierarchy();
        }

        if(currentStep < totalSteps){
            currentStep++;
            showStep(currentStep);
        }
    }
);

document
.getElementById(
    "previousStep"
)
.addEventListener(
    "click",
    () => {

        if(currentStep > 1){
            currentStep--;
            showStep(currentStep);
        }
    }
);

document
.getElementById(
    "generateSimulation"
)
.addEventListener(
    "click",
    () => {
        generateSimulationFile();
    }
);

document
.getElementById(
    "loadSampleSchema"
)
.addEventListener(
    "click",
    loadSampleSchema
);

buildHierarchy();

loadSchemaProfiles();

showStep(1);
