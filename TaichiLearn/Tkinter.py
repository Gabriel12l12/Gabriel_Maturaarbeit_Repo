if simulationRunning:
    with gui.sub_window("Simulation", x=0, y=0, width=0.3, height=0.25):

            if gui.button("Stop"):
                simulationRunning = False
        
    if setup:
                
        ResetTaichiFields()

        InitializePallets(statePallete)
        
        startKrankeSicher = min(startKranke, width * height)
        
        KrankheitsAusbruch(width, height, grid, erfolgreichInfiziert, startKrankeSicher)
    
        InitializeAge(width, height, grid, demografie)
   
        InitializeHouseholds(width, height, grid, householdData)
        
        InitializeSocial(width, height, grid, socialInput)
               

        for i in range(10):
            CreateHouseholdsStep(width, height, grid)
                
        print("Setup fertig")
        setup = False
        wechsel = False

    #pointerSwap
    if wechsel:
        pWrite = grid
        pRead  = gridAlt
        wechsel = False
    else:
        pWrite = gridAlt
        pRead  = grid
        wechsel = True

            
    Calculation(width, height, pWrite, pRead, baseTransmissionrate * 0.01, householdFactor, mortalityrate * 0.01, ageFactor, incubationTime, recoveryTime, maxRadius, referenzAlter)
         
    ColorCells(width, height, grid, gridColorField, statePallete)
    BildRunterskallieren(width, height, renderWidth, renderHeight, gridColorField, renderColorField)

    tag += 1

    ZaehleStatusNeu(width, height, pWrite)

    simulationsverlauf.append([durchlauf, tag, statusCounts[0], statusCounts[1], statusCounts[2], statusCounts[3]])


    print(f"Tag {tag} | Gesund: {statusCounts[0]}  Krank: {statusCounts[1]}  Immun: {statusCounts[2]}  Tot: {statusCounts[3]}")

    #Ende vom Durchlauf
    if statusCounts[1] == 0:
        name = HeadlessOrdnerPath + headlessName + csvSpeicherName + str(durchlauf)
        writeCSV(simulationsverlauf, name, seed)
        simulationRunning == False

 















             if simulationRunning:
        with gui.sub_window("Simulation", x=0, y=0, width=0.3, height=0.25):

            if gui.button("Stop"):
                simulationRunning = False

        #Fields mit Werten fuellen
        if setup:

            TaichiFieldsDefinieren(Cell, width, height, renderWidth, renderHeight)

            InitializePallets(statePallete)

            startKrankeSicher = min(startKranke, width * height)
            KrankheitsAusbruch(width, height, grid, erfolgreichInfiziert, startKrankeSicher)

            InitializeAge(width, height, grid, demografie)

            InitializeHouseholds(width, height, grid, householdData)

            InitializeSocial(width, height, grid, socialInput)

            for i in range(10):
                CreateHouseholdsStep(width, height, grid)

            setup = False

        Calculation(width, height, grid, gridAlt, baseTransmissionrate * 0.01, householdFactor, mortalityrate * 0.01, ageFactor, incubationTime, recoveryTime, maxRadius, referenzAlter)

        #Grafische Darstellung
        ColorCells(width, height, grid, gridColorField, statePallete)
        BildRunterskallieren(width, height, renderWidth, renderHeight, gridColorField, renderColorField)


        tag += 1
