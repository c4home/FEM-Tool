package require Tk

# -----------------------------------------------------------------
# 1. User Interface (UI) Setup
# -----------------------------------------------------------------
catch {destroy .exportUI}
toplevel .exportUI
wm title .exportUI "XYZ Extreme Exporter & Stress Exporter"
wm geometry .exportUI "450x700"
wm attributes .exportUI -topmost 1

# --- Part 1: Displacement Extreme Exporter ---
label .exportUI.lbl -text "Export EXTREME X, Y, Z, Mag per Subcase\n1. Plot Displacement contour first.\n2. Click Export."
pack .exportUI.lbl -pady 10

button .exportUI.btn -text "Export Displacements" -command ExportExtremeRobust
pack .exportUI.btn -pady 5 -padx 30 -fill x

# --- Part 2: Stress Exporter ---
frame .exportUI.sep0 -height 2 -borderwidth 1 -relief sunken
pack .exportUI.sep0 -fill x -padx 10 -pady 10

frame .exportUI.frmSet
pack .exportUI.frmSet -pady 5
label .exportUI.frmSet.lbl -text "Elements Selection Format:\n'all' -> All elements\n'1-100' -> Element ID range\n'id 5' -> Element ID 5\n'selectionset == 5' -> User Set ID 5\n'component == Part1' -> Component name" -justify left
pack .exportUI.frmSet.lbl -side left -padx 10
entry .exportUI.frmSet.ent -textvariable ::user_elem_sel -width 25
set ::user_elem_sel "selectionset == 5"
pack .exportUI.frmSet.ent -side left -padx 5

button .exportUI.btnStress -text "Stress VonMises, Max/Min Prin Stress " -command ExportStressForSet
pack .exportUI.btnStress -pady 10 -padx 30 -fill x

# --- Part 3: Failure Index Exporter ---
frame .exportUI.sep1 -height 2 -borderwidth 1 -relief sunken
pack .exportUI.sep1 -fill x -padx 10 -pady 10

button .exportUI.btnFailure -text "Failure Index" -command ExportFailureIndexForSet
pack .exportUI.btnFailure -pady 10 -padx 30 -fill x

# --- Part 4: Inter Laminar Stress Exporter ---
frame .exportUI.sep3 -height 2 -borderwidth 1 -relief sunken
pack .exportUI.sep3 -fill x -padx 10 -pady 10

button .exportUI.btnILS -text "Stress Inter Laminar" -command ExportInterLaminarStressForSet
pack .exportUI.btnILS -pady 10 -padx 30 -fill x

# --- Part 5: Stress Extreme Layer Exporter ---
frame .exportUI.sep4 -height 2 -borderwidth 1 -relief sunken
pack .exportUI.sep4 -fill x -padx 10 -pady 10

frame .exportUI.frmAllow
pack .exportUI.frmAllow -pady 5

label .exportUI.frmAllow.lblFsu -text "Fsu"
entry .exportUI.frmAllow.entFsu -textvariable ::Fsu -width 10
label .exportUI.frmAllow.lblFcu -text "Fcu"
entry .exportUI.frmAllow.entFcu -textvariable ::Fcu -width 10
label .exportUI.frmAllow.lblFtu -text "Ftu"
entry .exportUI.frmAllow.entFtu -textvariable ::Ftu -width 10

pack .exportUI.frmAllow.lblFsu .exportUI.frmAllow.entFsu \
     .exportUI.frmAllow.lblFcu .exportUI.frmAllow.entFcu \
     .exportUI.frmAllow.lblFtu .exportUI.frmAllow.entFtu \
     -side left -padx 5

set ::Fsu 44.66
set ::Fcu 30.0
set ::Ftu 30.0

button .exportUI.btnStressExt -text "Stress XX, YY, ZZ, XY, ZX, YZ" -command ExportStressExtremeLayer
pack .exportUI.btnStressExt -pady 10 -padx 30 -fill x

# --- Part 6: Stress Extreme Layer Exporter (ZX & YZ Only) ---
frame .exportUI.sep5 -height 2 -borderwidth 1 -relief sunken
pack .exportUI.sep5 -fill x -padx 10 -pady 10

frame .exportUI.frmAllowZXYZ
pack .exportUI.frmAllowZXYZ -pady 5

label .exportUI.frmAllowZXYZ.lblFzx -text "Fzx"
entry .exportUI.frmAllowZXYZ.entFzx -textvariable ::Fzx -width 10
label .exportUI.frmAllowZXYZ.lblFyz -text "Fyz"
entry .exportUI.frmAllowZXYZ.entFyz -textvariable ::Fyz -width 10

pack .exportUI.frmAllowZXYZ.lblFzx .exportUI.frmAllowZXYZ.entFzx \
     .exportUI.frmAllowZXYZ.lblFyz .exportUI.frmAllowZXYZ.entFyz \
     -side left -padx 5

set ::Fzx 0.5
set ::Fyz 0.98

button .exportUI.btnStressExtXZYZ -text "Stress ZX, YZ" -command ExportStressExtremeLayerZXYZ
pack .exportUI.btnStressExtXZYZ -pady 10 -padx 30 -fill x

# --- Part 7: Fastener Force Exporter (1D Elements) ---
frame .exportUI.sep6 -height 2 -borderwidth 1 -relief sunken
pack .exportUI.sep6 -fill x -padx 10 -pady 10

frame .exportUI.frmFastener
pack .exportUI.frmFastener -pady 5

label .exportUI.frmFastener.lblFt -text "Ft"
entry .exportUI.frmFastener.entFt -textvariable ::Ft -width 10
label .exportUI.frmFastener.lblFs -text "Fs"
entry .exportUI.frmFastener.entFs -textvariable ::Fs -width 10

pack .exportUI.frmFastener.lblFt .exportUI.frmFastener.entFt \
     .exportUI.frmFastener.lblFs .exportUI.frmFastener.entFs \
     -side left -padx 5

set ::Ft 1000.0
set ::Fs 1000.0

button .exportUI.btnFastener -text "1D Element Forces (X, Y, Z)" -command ExportFastenerForces
pack .exportUI.btnFastener -pady 10 -padx 30 -fill x

# -----------------------------------------------------------------
# Helper Function to Find Extreme Value & Calculate RF
# -----------------------------------------------------------------

proc SafeRF {allowable stress} {
    if {$stress eq ""} { return "N/A" }
    if {![string is double -strict $allowable]} { return "N/A" }
    if {![string is double -strict $stress]} { return "N/A" }
    if {$stress == 0} { return "N/A" }
    return [format "%.3f" [expr {abs($allowable / $stress)}]]
}

proc GetExtreme {max_val min_val} {
    if {[expr abs($min_val)] > [expr abs($max_val)]} {
        return [format "%.2f" $min_val]
    } else {
        return [format "%.2f" $max_val]
    }
}

# -----------------------------------------------------------------
# 2. Main Procedure: Displacement Extremes
# -----------------------------------------------------------------
proc ExportExtremeRobust {} {
    foreach h {sess proj page win cli mod res cont leg} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save Extreme Components"]
    if {$filepath == ""} { return }

    set fp [open $filepath w]
    puts $fp "Loadcase_ID,Loadcase_Name,X_Extreme,Y_Extreme,Z_Extreme,Mag_Max"

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont

    set subcase_list [res GetSubcaseList "Base"]

    set first_sub [lindex $subcase_list 0]
    set compList [res GetDataComponentList $first_sub "Displacements"]

    set mag_str "Mag"
    set x_str "X"
    set y_str "Y"
    set z_str "Z"

    foreach comp $compList {
        set c_low [string tolower $comp]
        if {$c_low == "mag"} { set mag_str $comp }
        if {$c_low == "x"} { set x_str $comp }
        if {$c_low == "y"} { set y_str $comp }
        if {$c_low == "z"} { set z_str $comp }
    }

    cli Draw

    foreach sub $subcase_list {
        res SetCurrentSubcase $sub

        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        # --- MAGNITUDE ---
        cont SetEnableState false
        cont SetDataComponent $mag_str
        cont SetEnableState true
        cli Draw
        cont GetLegendHandle leg
        set mag_max [format "%.2f" [leg GetMax]]
        leg ReleaseHandle

        # --- X COMPONENT ---
        cont SetEnableState false
        cont SetDataComponent $x_str
        cont SetEnableState true
        cli Draw
        cont GetLegendHandle leg
        set x_ext [GetExtreme [leg GetMax] [leg GetMin]]
        leg ReleaseHandle

        # --- Y COMPONENT ---
        cont SetEnableState false
        cont SetDataComponent $y_str
        cont SetEnableState true
        cli Draw
        cont GetLegendHandle leg
        set y_ext [GetExtreme [leg GetMax] [leg GetMin]]
        leg ReleaseHandle

        # --- Z COMPONENT ---
        cont SetEnableState false
        cont SetDataComponent $z_str
        cont SetEnableState true
        cli Draw
        cont GetLegendHandle leg
        set z_ext [GetExtreme [leg GetMax] [leg GetMin]]
        leg ReleaseHandle

        puts $fp "$sub,$safe_sub_name,$x_ext,$y_ext,$z_ext,$mag_max"
    }

    cont SetEnableState false
    cont SetDataComponent $mag_str
    cont SetEnableState true
    cli Draw

    close $fp
    tk_messageBox -message "Export complete!\nSaved to: $filepath" -type ok -parent .exportUI

    foreach h {cont res mod cli win page proj sess} { catch {$h ReleaseHandle} }
}

# -----------------------------------------------------------------
# 3. New Procedure: Export EXTREME Stresses per Subcase for Selection
# -----------------------------------------------------------------
proc ExportStressForSet {} {
    global user_elem_sel

    foreach h {sess proj page win cli mod res cont qry iter elem_set} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save Extreme Stresses"]
    if {$filepath == ""} { return }

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    set sel_id [mod AddSelectionSet element]
    mod GetSelectionSetHandle elem_set $sel_id

    # Evaluate selection safely
    if {[catch {eval "elem_set Add \"$user_elem_sel\""}]} {
        tk_messageBox -message "Invalid selection: '$user_elem_sel'. Exporting 'all'. Make sure to use syntax like 'selectionset == 5'." -parent .exportUI
        elem_set Add all
    }

    set num_elems [elem_set GetSize]
    if {$num_elems == 0} {
        tk_messageBox -message "Warning: Your selection '$user_elem_sel' resulted in 0 elements. The exported file will contain N/A." -parent .exportUI -icon warning
    }

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont
    mod GetQueryCtrlHandle qry

    # Try to identify component names assuming Data Type is already Stress
    set subcase_list [res GetSubcaseList "Base"]
    set first_sub [lindex $subcase_list 0]
    set compList [res GetDataComponentList $first_sub "Stresses"]
    if {[llength $compList] == 0} {
        set compList [res GetDataComponentList $first_sub "Stress"]
    }

    set c_von "vonMises"
    set c_max "maxPrincipal"
    set c_min "minPrincipal"

    foreach c $compList {
        set cl [string tolower $c]

        # STRICT check to avoid grabbing Signed Von Mises
        if {[string match "*von*mises*" $cl]} { 
            # If it's pure vonMises and not signed
            if {![string match "*signed*" $cl]} {
                set c_von $c 
            }
        }

        if {[string match "*max*principal*" $cl] || [string match "*p1*major*" $cl]} { set c_max $c }
        if {[string match "*min*principal*" $cl] || [string match "*p3*minor*" $cl]} { set c_min $c }
    }

    qry SetSelectionSet $sel_id
    qry SetQuery "element.id contour.value"

    set fp [open $filepath w]
    puts $fp "Loadcase_ID,Loadcase_Name,Max_VonMises,Max_MaxPrincipal,Min_MinPrincipal"

    # Tracking variables for global extremes across all loadcases
    set g_max_von ""
    set g_max_p1 ""
    set g_min_p3 ""

    foreach sub $subcase_list {
        res SetCurrentSubcase $sub
        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        set max_von ""
        set max_p1 ""
        set min_p3 ""

        if {$num_elems > 0} {
            # VON MISES (Layer = Max)
            cont SetEnableState false
            catch {cont SetDataComponent $c_von}
            catch {cont SetShellLayer "Max"}
            cont SetEnableState true
            cli Draw
            qry GetIteratorHandle iter
            for {iter First} {[iter Valid]} {iter Next} {
                set val [lindex [iter GetDataList] 1]
                if {[string is double -strict $val]} {
                    if {$max_von == "" || $val > $max_von} { set max_von $val }
                }
            }
            iter ReleaseHandle

            # MAX PRINCIPAL (Layer = Max)
            cont SetEnableState false
            catch {cont SetDataComponent $c_max}
            catch {cont SetShellLayer "Max"}
            cont SetEnableState true
            cli Draw
            qry GetIteratorHandle iter
            for {iter First} {[iter Valid]} {iter Next} {
                set val [lindex [iter GetDataList] 1]
                if {[string is double -strict $val]} {
                    if {$max_p1 == "" || $val > $max_p1} { set max_p1 $val }
                }
            }
            iter ReleaseHandle

            # MIN PRINCIPAL (Layer = Min)
            cont SetEnableState false
            catch {cont SetDataComponent $c_min}
            catch {cont SetShellLayer "Min"}
            cont SetEnableState true
            cli Draw
            qry GetIteratorHandle iter
            for {iter First} {[iter Valid]} {iter Next} {
                set val [lindex [iter GetDataList] 1]
                if {[string is double -strict $val]} {
                    if {$min_p3 == "" || $val < $min_p3} { set min_p3 $val }
                }
            }
            iter ReleaseHandle
        }

        # Update Globals
        if {$max_von != ""} { if {$g_max_von == "" || $max_von > $g_max_von} { set g_max_von $max_von } }
        if {$max_p1 != ""} { if {$g_max_p1 == "" || $max_p1 > $g_max_p1} { set g_max_p1 $max_p1 } }
        if {$min_p3 != ""} { if {$g_min_p3 == "" || $min_p3 < $g_min_p3} { set g_min_p3 $min_p3 } }

        # Format for CSV
        if {$max_von != ""} { set str_von [format "%.2f" $max_von] } else { set str_von "N/A" }
        if {$max_p1 != ""} { set str_p1 [format "%.2f" $max_p1] } else { set str_p1 "N/A" }
        if {$min_p3 != ""} { set str_p3 [format "%.2f" $min_p3] } else { set str_p3 "N/A" }

        puts $fp "$sub,$safe_sub_name,$str_von,$str_p1,$str_p3"
    }

    # Write a summary row at the bottom for the absolute extremes
    puts $fp "---,---,---,---,---"
    if {$g_max_von != ""} { set g_max_von [format "%.2f" $g_max_von] } else { set g_max_von "N/A" }
    if {$g_max_p1 != ""} { set g_max_p1 [format "%.2f" $g_max_p1] } else { set g_max_p1 "N/A" }
    if {$g_min_p3 != ""} { set g_min_p3 [format "%.2f" $g_min_p3] } else { set g_min_p3 "N/A" }

    puts $fp "GLOBAL_EXTREMES,ALL_SUBCASES,$g_max_von,$g_max_p1,$g_min_p3"

    close $fp

    tk_messageBox -message "Stress Export complete!\nSaved to: $filepath" -type ok -parent .exportUI

    mod RemoveSelectionSet $sel_id
    foreach h {cont res mod cli win page proj sess qry elem_set iter} { catch {$h ReleaseHandle} }
}
# -----------------------------------------------------------------
# 4. New Procedure: Export Failure Index per Subcase for Selection
# -----------------------------------------------------------------
proc ExportFailureIndexForSet {} {
    global user_elem_sel

    foreach h {sess proj page win cli mod res cont qry iter elem_set} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save Extreme Failure Indices"]
    if {$filepath == ""} { return }

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    set sel_id [mod AddSelectionSet element]
    mod GetSelectionSetHandle elem_set $sel_id

    # Evaluate selection safely
    if {[catch {eval "elem_set Add \"$user_elem_sel\""}]} {
        tk_messageBox -message "Invalid selection: '$user_elem_sel'. Exporting 'all'." -parent .exportUI
        elem_set Add all
    }

    set num_elems [elem_set GetSize]
    if {$num_elems == 0} {
        tk_messageBox -message "Warning: Your selection resulted in 0 elements." -parent .exportUI -icon warning
    }

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont
    mod GetQueryCtrlHandle qry

    set subcase_list [res GetSubcaseList "Base"]
    set first_sub [lindex $subcase_list 0]
    
    # ---------------------------------------------------------
    # AUTO-DETECT EXACT INTERNAL STRINGS
    # ---------------------------------------------------------
    set actual_type "Failure Index (s)"
    set actual_comp "for direct Stress"
    
    if {![catch {res GetDataTypeList $first_sub} all_types]} {
        foreach t $all_types {
            if {[string match -nocase "*Failure*Index*" $t]} {
                set actual_type $t
                break
            }
        }
        
        if {![catch {res GetDataComponentList $first_sub $actual_type} all_comps]} {
            foreach c $all_comps {
                if {[string match -nocase "*direct*Stress*" $c]} {
                    set actual_comp $c
                    break
                }
            }
        }
    }
    # ---------------------------------------------------------

    qry SetSelectionSet $sel_id
    qry SetQuery "element.id contour.value"

    set fp [open $filepath w]
    puts $fp "Loadcase_ID,Loadcase_Name,Max_Failure_Index,RF"

    set g_max_fi ""

    foreach sub $subcase_list {
        res SetCurrentSubcase $sub
        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        set max_fi ""

        if {$num_elems > 0} {
            cont SetEnableState false
            
            # Apply dynamically found criteria (removed 'catch' so it forces the change)
            cont SetDataType $actual_type
            cont SetDataComponent $actual_comp
            cont SetShellLayer "Max"
            
            cont SetEnableState true
            cli Draw
            
            qry GetIteratorHandle iter
            for {iter First} {[iter Valid]} {iter Next} {
                set val [lindex [iter GetDataList] 1]
                if {[string is double -strict $val]} {
                    if {$max_fi == "" || $val > $max_fi} { set max_fi $val }
                }
            }
            iter ReleaseHandle
        }

        # Update Globals
        if {$max_fi != ""} { if {$g_max_fi == "" || $max_fi > $g_max_fi} { set g_max_fi $max_fi } }

        # Format for CSV and Calculate RF
        if {$max_fi != ""} { 
            set str_fi [format "%.4f" $max_fi] 
            if {$max_fi > 0} {
                set str_rf [format "%.3f" [expr {1.0 / sqrt($max_fi)}]]
            } else {
                set str_rf "N/A"
            }
        } else { 
            set str_fi "N/A"
            set str_rf "N/A"
        }

        puts $fp "$sub,$safe_sub_name,$str_fi,$str_rf"
    }

    puts $fp "---,---,---,---"
    
    if {$g_max_fi != ""} { 
        if {$g_max_fi > 0} {
            set g_rf [format "%.3f" [expr {1.0 / sqrt($g_max_fi)}]]
        } else {
            set g_rf "N/A"
        }
        set g_max_fi [format "%.4f" $g_max_fi] 
    } else { 
        set g_max_fi "N/A" 
        set g_rf "N/A"
    }

    puts $fp "GLOBAL_EXTREMES,ALL_SUBCASES,$g_max_fi,$g_rf"
    close $fp

    # I've added a debug readout here so you can verify what strings it actually used
    tk_messageBox -message "Failure Index Export complete!\n\nDebug Info:\nType Used: '$actual_type'\nComp Used: '$actual_comp'" -type ok -parent .exportUI

    mod RemoveSelectionSet $sel_id
    foreach h {cont res mod cli win page proj sess qry elem_set iter} { catch {$h ReleaseHandle} }
}

# -----------------------------------------------------------------
# 5. New Procedure: Export Inter Laminar Stress per Subcase for Selection
# -----------------------------------------------------------------
proc ExportInterLaminarStressForSet {} {
    global user_elem_sel

    foreach h {sess proj page win cli mod res cont qry iter elem_set} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save Extreme Inter Laminar Stresses"]
    if {$filepath == ""} { return }

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    set sel_id [mod AddSelectionSet element]
    mod GetSelectionSetHandle elem_set $sel_id

    # Evaluate selection safely
    if {[catch {eval "elem_set Add \"$user_elem_sel\""}]} {
        tk_messageBox -message "Invalid selection: '$user_elem_sel'. Exporting 'all'." -parent .exportUI
        elem_set Add all
    }

    set num_elems [elem_set GetSize]
    if {$num_elems == 0} {
        tk_messageBox -message "Warning: Your selection resulted in 0 elements." -parent .exportUI -icon warning
    }

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont
    mod GetQueryCtrlHandle qry

    set subcase_list [res GetSubcaseList "Base"]
    set first_sub [lindex $subcase_list 0]

    # AUTO-DETECT EXACT INTERNAL STRINGS
    set actual_type "Inter Laminar Stress (s)"
    set comp_yz "Shear YZ"
    set comp_xz "Shear XZ"

    if {![catch {res GetDataTypeList $first_sub} all_types]} {
        foreach t $all_types {
            if {[string match -nocase "*Inter*Laminar*Stress*" $t]} {
                set actual_type $t
                break
            }
        }
    }

    if {![catch {res GetDataComponentList $first_sub $actual_type} all_comps]} {
        foreach c $all_comps {
            if {[string match -nocase "*yz*" $c]} { set comp_yz $c }
            if {[string match -nocase "*xz*" $c]} { set comp_xz $c }
        }
    }

    qry SetSelectionSet $sel_id
    qry SetQuery "element.id contour.value"

    set fp [open $filepath w]
    # UPDATED CSV HEADER ORDER
    puts $fp "Loadcase_ID,Loadcase_Name,Max_Shear_XZ,Max_Shear_YZ,Min_Shear_XZ,Min_Shear_YZ"

    set g_max_yz ""; set g_min_yz ""
    set g_max_xz ""; set g_min_xz ""

    foreach sub $subcase_list {
        res SetCurrentSubcase $sub
        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        set max_yz ""; set min_yz ""
        set max_xz ""; set min_xz ""

        if {$num_elems > 0} {
            cont SetEnableState false
            cont SetDataType $actual_type

            # --- SHEAR YZ ---
            if {![catch {cont SetDataComponent $comp_yz}]} {
                catch {cont SetShellLayer "Max"}
                cont SetEnableState true
                cli Draw
                qry GetIteratorHandle iter
                for {iter First} {[iter Valid]} {iter Next} {
                    set val [lindex [iter GetDataList] 1]
                    if {[string is double -strict $val]} {
                        if {$max_yz == "" || $val > $max_yz} { set max_yz $val }
                        if {$min_yz == "" || $val < $min_yz} { set min_yz $val }
                    }
                }
                iter ReleaseHandle
            }

            # --- SHEAR XZ ---
            cont SetEnableState false
            if {![catch {cont SetDataComponent $comp_xz}]} {
                catch {cont SetShellLayer "Max"}
                cont SetEnableState true
                cli Draw
                qry GetIteratorHandle iter
                for {iter First} {[iter Valid]} {iter Next} {
                    set val [lindex [iter GetDataList] 1]
                    if {[string is double -strict $val]} {
                        if {$max_xz == "" || $val > $max_xz} { set max_xz $val }
                        if {$min_xz == "" || $val < $min_xz} { set min_xz $val }
                    }
                }
                iter ReleaseHandle
            }
        }

        # Update Globals
        if {$max_yz != ""} { if {$g_max_yz == "" || $max_yz > $g_max_yz} { set g_max_yz $max_yz } }
        if {$min_yz != ""} { if {$g_min_yz == "" || $min_yz < $g_min_yz} { set g_min_yz $min_yz } }
        if {$max_xz != ""} { if {$g_max_xz == "" || $max_xz > $g_max_xz} { set g_max_xz $max_xz } }
        if {$min_xz != ""} { if {$g_min_xz == "" || $min_xz < $g_min_xz} { set g_min_xz $min_xz } }

        # Format for CSV
        if {$max_yz != ""} { set str_max_yz [format "%.3f" $max_yz] } else { set str_max_yz "N/A" }
        if {$min_yz != ""} { set str_min_yz [format "%.3f" $min_yz] } else { set str_min_yz "N/A" }
        if {$max_xz != ""} { set str_max_xz [format "%.3f" $max_xz] } else { set str_max_xz "N/A" }
        if {$min_xz != ""} { set str_min_xz [format "%.3f" $min_xz] } else { set str_min_xz "N/A" }

        # UPDATED LOOP OUTPUT ORDER
        puts $fp "$sub,$safe_sub_name,$str_max_xz,$str_max_yz,$str_min_xz,$str_min_yz"
    }

    # Summary Row
    puts $fp "---,---,---,---,---,---"
    if {$g_max_yz != ""} { set g_max_yz [format "%.3f" $g_max_yz] } else { set g_max_yz "N/A" }
    if {$g_min_yz != ""} { set g_min_yz [format "%.3f" $g_min_yz] } else { set g_min_yz "N/A" }
    if {$g_max_xz != ""} { set g_max_xz [format "%.3f" $g_max_xz] } else { set g_max_xz "N/A" }
    if {$g_min_xz != ""} { set g_min_xz [format "%.3f" $g_min_xz] } else { set g_min_xz "N/A" }

    # UPDATED GLOBAL EXTREMES OUTPUT ORDER
    puts $fp "GLOBAL_EXTREMES,ALL_SUBCASES,$g_max_xz,$g_max_yz,$g_min_xz,$g_min_yz"
    close $fp

    tk_messageBox -message "Inter Laminar Stress Export complete!\nSaved to: $filepath" -type ok -parent .exportUI

    mod RemoveSelectionSet $sel_id
    foreach h {cont res mod cli win page proj sess qry elem_set iter} { catch {$h ReleaseHandle} }
}

# -----------------------------------------------------------------
# 6. New Procedure: Export Extreme Layer Normal/Shear Stresses
# -----------------------------------------------------------------
proc ExportStressExtremeLayer {} {
    global user_elem_sel Fsu Fcu Ftu

    foreach h {sess proj page win cli mod res cont qry iter elem_set} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save Extreme Normal and Shear Stresses"]
    if {$filepath == ""} { return }

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    set sel_id [mod AddSelectionSet element]
    mod GetSelectionSetHandle elem_set $sel_id

    # Evaluate selection safely
    if {[catch {eval "elem_set Add \"$user_elem_sel\""}]} {
        tk_messageBox -message "Invalid selection: '$user_elem_sel'. Exporting 'all'." -parent .exportUI
        elem_set Add all
    }

    set num_elems [elem_set GetSize]
    if {$num_elems == 0} {
        tk_messageBox -message "Warning: Your selection resulted in 0 elements." -parent .exportUI -icon warning
    }

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont
    mod GetQueryCtrlHandle qry

    set subcase_list [res GetSubcaseList "Base"]
    set first_sub [lindex $subcase_list 0]

    # Try to identify component names assuming Data Type is already Stress
    set actual_type "Stresses"
    set compList [res GetDataComponentList $first_sub $actual_type]
    if {[llength $compList] == 0} {
        set actual_type "Stress"
        set compList [res GetDataComponentList $first_sub $actual_type]
    }

    # Initialize component variables
    set c_xx "XX"; set c_yy "YY"; set c_zz "ZZ"
    set c_xy "XY"; set c_zx "ZX"; set c_yz "YZ"

    foreach c $compList {
        set cl [string tolower $c]
        if {[string match "*xx*" $cl] && ![string match "*max*" $cl]} { set c_xx $c }
        if {[string match "*yy*" $cl] && ![string match "*max*" $cl]} { set c_yy $c }
        if {[string match "*zz*" $cl] && ![string match "*max*" $cl]} { set c_zz $c }
        if {[string match "*xy*" $cl] && ![string match "*max*" $cl]} { set c_xy $c }
        if {[string match "*zx*" $cl] && ![string match "*max*" $cl]} { set c_zx $c }
        if {[string match "*yz*" $cl] && ![string match "*max*" $cl]} { set c_yz $c }
    }

    qry SetSelectionSet $sel_id
    qry SetQuery "element.id contour.value"

    set fp [open $filepath w]
    
    # UPDATED COLUMN ORDER HERE
    puts $fp "Loadcase_ID,Loadcase_Name,Max_XX,RF_Max_XX,Max_YY,RF_Max_YY,Max_ZZ,RF_Max_ZZ,Max_XY,RF_Max_XY,Max_ZX,RF_Max_ZX,Max_YZ,RF_Max_YZ,Min_XX,RF_Min_XX,Min_YY,RF_Min_YY,Min_ZZ,RF_Min_ZZ,Min_XY,RF_Min_XY,Min_ZX,RF_Min_ZX,Min_YZ,RF_Min_YZ"


    # Global variables
    set g_max_xx ""; set g_min_xx ""
    set g_max_yy ""; set g_min_yy ""
    set g_max_zz ""; set g_min_zz ""
    set g_max_xy ""; set g_min_xy ""
    set g_max_zx ""; set g_min_zx ""
    set g_max_yz ""; set g_min_yz ""

    set components [list $c_xx $c_yy $c_zz $c_xy $c_zx $c_yz]
    
    foreach sub $subcase_list {
        res SetCurrentSubcase $sub
        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        # Local variables
        set l_max [list "" "" "" "" "" ""]
        set l_min [list "" "" "" "" "" ""]

        if {$num_elems > 0} {
            for {set i 0} {$i < 6} {incr i} {
                cont SetEnableState false
                cont SetDataType $actual_type
                
                if {![catch {cont SetDataComponent [lindex $components $i]}]} {
                    catch {cont SetShellLayer "Extreme"}
                    catch {cont SetResultSystem -1}
                    cont SetEnableState true
                    cli Draw
                    
                    qry GetIteratorHandle iter
                    for {iter First} {[iter Valid]} {iter Next} {
                        set val [lindex [iter GetDataList] 1]
                        if {[string is double -strict $val]} {
                            set c_max [lindex $l_max $i]
                            set c_min [lindex $l_min $i]
                            
                            if {$c_max == "" || $val > $c_max} { lset l_max $i $val }
                            if {$c_min == "" || $val < $c_min} { lset l_min $i $val }
                        }
                    }
                    iter ReleaseHandle
                }
            }
        }

        # Update Globals & Format for CSV Output
        set str_max_out ""
        set str_min_out ""

        for {set i 0} {$i < 6} {incr i} {
            set c_max [lindex $l_max $i]
            set c_min [lindex $l_min $i]

            # Globals update
            if {$i == 0} {
                if {$c_max != ""} { if {$g_max_xx == "" || $c_max > $g_max_xx} { set g_max_xx $c_max } }
                if {$c_min != ""} { if {$g_min_xx == "" || $c_min < $g_min_xx} { set g_min_xx $c_min } }
            } elseif {$i == 1} {
                if {$c_max != ""} { if {$g_max_yy == "" || $c_max > $g_max_yy} { set g_max_yy $c_max } }
                if {$c_min != ""} { if {$g_min_yy == "" || $c_min < $g_min_yy} { set g_min_yy $c_min } }
            } elseif {$i == 2} {
                if {$c_max != ""} { if {$g_max_zz == "" || $c_max > $g_max_zz} { set g_max_zz $c_max } }
                if {$c_min != ""} { if {$g_min_zz == "" || $c_min < $g_min_zz} { set g_min_zz $c_min } }
            } elseif {$i == 3} {
                if {$c_max != ""} { if {$g_max_xy == "" || $c_max > $g_max_xy} { set g_max_xy $c_max } }
                if {$c_min != ""} { if {$g_min_xy == "" || $c_min < $g_min_xy} { set g_min_xy $c_min } }
            } elseif {$i == 4} {
                if {$c_max != ""} { if {$g_max_zx == "" || $c_max > $g_max_zx} { set g_max_zx $c_max } }
                if {$c_min != ""} { if {$g_min_zx == "" || $c_min < $g_min_zx} { set g_min_zx $c_min } }
            } elseif {$i == 5} {
                if {$c_max != ""} { if {$g_max_yz == "" || $c_max > $g_max_yz} { set g_max_yz $c_max } }
                if {$c_min != ""} { if {$g_min_yz == "" || $c_min < $g_min_yz} { set g_min_yz $c_min } }
            }

            set str_max [expr {$c_max != "" ? [format "%.3f" $c_max] : "N/A"}]
            set str_min [expr {$c_min != "" ? [format "%.3f" $c_min] : "N/A"}]

            # RF rules requested by user
            set rf_max [SafeRF $Ftu $c_max]

            if {$i <= 2} {
                set rf_min [SafeRF $Fcu $c_min]
            } else {
                set rf_min [SafeRF $Ftu $c_min]
            }

            append str_max_out ",$str_max,$rf_max"
            append str_min_out ",$str_min,$rf_min"
        }

        puts $fp "$sub,$safe_sub_name$str_max_out$str_min_out"
    }

    # Summary Row Format

    set g_str_max_xx [expr {$g_max_xx != "" ? [format "%.3f" $g_max_xx] : "N/A"}]
    set g_str_min_xx [expr {$g_min_xx != "" ? [format "%.3f" $g_min_xx] : "N/A"}]
    set g_str_max_yy [expr {$g_max_yy != "" ? [format "%.3f" $g_max_yy] : "N/A"}]
    set g_str_min_yy [expr {$g_min_yy != "" ? [format "%.3f" $g_min_yy] : "N/A"}]
    set g_str_max_zz [expr {$g_max_zz != "" ? [format "%.3f" $g_max_zz] : "N/A"}]
    set g_str_min_zz [expr {$g_min_zz != "" ? [format "%.3f" $g_min_zz] : "N/A"}]
    set g_str_max_xy [expr {$g_max_xy != "" ? [format "%.3f" $g_max_xy] : "N/A"}]
    set g_str_min_xy [expr {$g_min_xy != "" ? [format "%.3f" $g_min_xy] : "N/A"}]
    set g_str_max_zx [expr {$g_max_zx != "" ? [format "%.3f" $g_max_zx] : "N/A"}]
    set g_str_min_zx [expr {$g_min_zx != "" ? [format "%.3f" $g_min_zx] : "N/A"}]
    set g_str_max_yz [expr {$g_max_yz != "" ? [format "%.3f" $g_max_yz] : "N/A"}]
    set g_str_min_yz [expr {$g_min_yz != "" ? [format "%.3f" $g_min_yz] : "N/A"}]

    set rf_g_max_xx [SafeRF $Ftu $g_max_xx]
    set rf_g_max_yy [SafeRF $Ftu $g_max_yy]
    set rf_g_max_zz [SafeRF $Ftu $g_max_zz]
    set rf_g_max_xy [SafeRF $Ftu $g_max_xy]
    set rf_g_max_zx [SafeRF $Ftu $g_max_zx]
    set rf_g_max_yz [SafeRF $Ftu $g_max_yz]

    set rf_g_min_xx [SafeRF $Fcu $g_min_xx]
    set rf_g_min_yy [SafeRF $Fcu $g_min_yy]
    set rf_g_min_zz [SafeRF $Fcu $g_min_zz]
    set rf_g_min_xy [SafeRF $Ftu $g_min_xy]
    set rf_g_min_zx [SafeRF $Ftu $g_min_zx]
    set rf_g_min_yz [SafeRF $Ftu $g_min_yz]

    puts $fp "---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---"

    puts $fp "GLOBAL_EXTREMES,ALL_SUBCASES,$g_str_max_xx,$rf_g_max_xx,$g_str_max_yy,$rf_g_max_yy,$g_str_max_zz,$rf_g_max_zz,$g_str_max_xy,$rf_g_max_xy,$g_str_max_zx,$rf_g_max_zx,$g_str_max_yz,$rf_g_max_yz,$g_str_min_xx,$rf_g_min_xx,$g_str_min_yy,$rf_g_min_yy,$g_str_min_zz,$rf_g_min_zz,$g_str_min_xy,$rf_g_min_xy,$g_str_min_zx,$rf_g_min_zx,$g_str_min_yz,$rf_g_min_yz"

    close $fp

    tk_messageBox -message "Normal & Shear Stresses Export complete!\nSaved to: $filepath" -type ok -parent .exportUI

    mod RemoveSelectionSet $sel_id
    foreach h {cont res mod cli win page proj sess qry elem_set iter} { catch {$h ReleaseHandle} }
}
# -----------------------------------------------------------------
# 7. New Procedure: Export Extreme Layer Normal/Shear Stresses (ZX & YZ Only)
# -----------------------------------------------------------------
proc ExportStressExtremeLayerZXYZ {} {
    global user_elem_sel Fzx Fyz

    foreach h {sess proj page win cli mod res cont qry iter elem_set} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save Extreme Normal and Shear Stresses (ZX & YZ)"]
    if {$filepath == ""} { return }

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    set sel_id [mod AddSelectionSet element]
    mod GetSelectionSetHandle elem_set $sel_id

    # Evaluate selection safely
    if {[catch {eval "elem_set Add \"$user_elem_sel\""}]} {
        tk_messageBox -message "Invalid selection: '$user_elem_sel'. Exporting 'all'." -parent .exportUI
        elem_set Add all
    }

    set num_elems [elem_set GetSize]
    if {$num_elems == 0} {
        tk_messageBox -message "Warning: Your selection resulted in 0 elements." -parent .exportUI -icon warning
    }

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont
    mod GetQueryCtrlHandle qry

    set subcase_list [res GetSubcaseList "Base"]
    set first_sub [lindex $subcase_list 0]

    # Try to identify component names assuming Data Type is already Stress
    set actual_type "Stresses"
    set compList [res GetDataComponentList $first_sub $actual_type]
    if {[llength $compList] == 0} {
        set actual_type "Stress"
        set compList [res GetDataComponentList $first_sub $actual_type]
    }

    # Initialize component variables
    set c_zx "ZX"; set c_yz "YZ"

    foreach c $compList {
        set cl [string tolower $c]
        if {[string match "*zx*" $cl] && ![string match "*max*" $cl]} { set c_zx $c }
        if {[string match "*yz*" $cl] && ![string match "*max*" $cl]} { set c_yz $c }
    }

    qry SetSelectionSet $sel_id
    qry SetQuery "element.id contour.value"

    set fp [open $filepath w]

    # OUTPUT COLUMN ORDER
    puts $fp "Loadcase_ID,Loadcase_Name,Max_ZX,RF_Max_ZX,Max_YZ,RF_Max_YZ,Min_ZX,RF_Min_ZX,Min_YZ,RF_Min_YZ"

    # Global variables
    set g_max_zx ""; set g_min_zx ""
    set g_max_yz ""; set g_min_yz ""

    set components [list $c_zx $c_yz]
    
    foreach sub $subcase_list {
        res SetCurrentSubcase $sub
        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        # Local variables
        set l_max [list "" ""]
        set l_min [list "" ""]

        if {$num_elems > 0} {
            for {set i 0} {$i < 2} {incr i} {
                cont SetEnableState false
                cont SetDataType $actual_type
                
                if {![catch {cont SetDataComponent [lindex $components $i]}]} {
                    catch {cont SetShellLayer "Extreme"}
                    catch {cont SetResultSystem -1}
                    cont SetEnableState true
                    cli Draw
                    
                    qry GetIteratorHandle iter
                    for {iter First} {[iter Valid]} {iter Next} {
                        set val [lindex [iter GetDataList] 1]
                        if {[string is double -strict $val]} {
                            set c_max [lindex $l_max $i]
                            set c_min [lindex $l_min $i]
                            
                            if {$c_max == "" || $val > $c_max} { lset l_max $i $val }
                            if {$c_min == "" || $val < $c_min} { lset l_min $i $val }
                        }
                    }
                    iter ReleaseHandle
                }
            }
        }

        # Update Globals & Format for CSV Output
        set str_max_out ""
        set str_min_out ""

        for {set i 0} {$i < 2} {incr i} {
            set c_max [lindex $l_max $i]
            set c_min [lindex $l_min $i]

            # Globals update
            if {$i == 0} {
                if {$c_max != ""} { if {$g_max_zx == "" || $c_max > $g_max_zx} { set g_max_zx $c_max } }
                if {$c_min != ""} { if {$g_min_zx == "" || $c_min < $g_min_zx} { set g_min_zx $c_min } }
            } elseif {$i == 1} {
                if {$c_max != ""} { if {$g_max_yz == "" || $c_max > $g_max_yz} { set g_max_yz $c_max } }
                if {$c_min != ""} { if {$g_min_yz == "" || $c_min < $g_min_yz} { set g_min_yz $c_min } }
            }

            # Local string format
            set str_max [expr {$c_max != "" ? [format "%.3f" $c_max] : "N/A"}]
            set str_min [expr {$c_min != "" ? [format "%.3f" $c_min] : "N/A"}]

            # RF Calculations
            if {$i == 0} {
                set rf_max [SafeRF $Fzx $c_max]
                set rf_min [SafeRF $Fzx $c_min]
            } else {
                set rf_max [SafeRF $Fyz $c_max]
                set rf_min [SafeRF $Fyz $c_min]
            }

            # Append maxes to one string, mins to another
            append str_max_out ",$str_max,$rf_max"
            append str_min_out ",$str_min,$rf_min"
        }

        # LOOP OUTPUT: Print all maxes first, then all mins
        puts $fp "$sub,$safe_sub_name$str_max_out$str_min_out"
    }

    # Summary Row Format
    set g_str_max_zx [expr {$g_max_zx != "" ? [format "%.3f" $g_max_zx] : "N/A"}]
    set g_str_min_zx [expr {$g_min_zx != "" ? [format "%.3f" $g_min_zx] : "N/A"}]
    set g_str_max_yz [expr {$g_max_yz != "" ? [format "%.3f" $g_max_yz] : "N/A"}]
    set g_str_min_yz [expr {$g_min_yz != "" ? [format "%.3f" $g_min_yz] : "N/A"}]

    set rf_g_max_zx [SafeRF $Fzx $g_max_zx]
    set rf_g_max_yz [SafeRF $Fyz $g_max_yz]
    set rf_g_min_zx [SafeRF $Fzx $g_min_zx]
    set rf_g_min_yz [SafeRF $Fyz $g_min_yz]

    puts $fp "---,---,---,---,---,---,---,---,---,---"

    # GLOBAL EXTREMES ROW: Print all maxes first, then all mins
    puts $fp "GLOBAL_EXTREMES,ALL_SUBCASES,$g_str_max_zx,$rf_g_max_zx,$g_str_max_yz,$rf_g_max_yz,$g_str_min_zx,$rf_g_min_zx,$g_str_min_yz,$rf_g_min_yz"

    close $fp

    tk_messageBox -message "ZX & YZ Stresses Export complete!\nSaved to: $filepath" -type ok -parent .exportUI

    mod RemoveSelectionSet $sel_id
    foreach h {cont res mod cli win page proj sess qry elem_set iter} { catch {$h ReleaseHandle} }
}

# -----------------------------------------------------------------
# 8. New Procedure: Export 1D Element Fastener Forces
# -----------------------------------------------------------------
proc ExportFastenerForces {} {
    global user_elem_sel Ft Fs

    foreach h {sess proj page win cli mod res cont qry iter elem_set} { catch {$h ReleaseHandle} }

    set filepath [tk_getSaveFile -filetypes {{{CSV Files} {.csv}}} -title "Save 1D Element Forces"]
    if {$filepath == ""} { return }

    hwi GetSessionHandle sess
    sess GetProjectHandle proj
    proj GetPageHandle page [proj GetActivePage]
    page GetWindowHandle win [page GetActiveWindow]

    win GetClientHandle cli
    cli GetModelHandle mod [cli GetActiveModel]

    set sel_id [mod AddSelectionSet element]
    mod GetSelectionSetHandle elem_set $sel_id

    # Evaluate selection safely
    if {[catch {eval "elem_set Add \"$user_elem_sel\""}]} {
        tk_messageBox -message "Invalid selection: '$user_elem_sel'. Exporting 'all'." -parent .exportUI
        elem_set Add all
    }

    set num_elems [elem_set GetSize]
    if {$num_elems == 0} {
        tk_messageBox -message "Warning: Your selection resulted in 0 elements." -parent .exportUI -icon warning
    }

    mod GetResultCtrlHandle res
    res GetContourCtrlHandle cont
    mod GetQueryCtrlHandle qry

    set subcase_list [res GetSubcaseList "Base"]
    set first_sub [lindex $subcase_list 0]

    # Auto-detect 1D Element Forces data type
    set actual_type "1D Element Forces"
    if {![catch {res GetDataTypeList $first_sub} all_types]} {
        foreach t $all_types {
            if {[string match -nocase "*1d*force*" $t]} { set actual_type $t; break }
        }
    }

    # Initialize component variables
    set compX "X"; set compY "Y"; set compZ "Z"
    if {![catch {res GetDataComponentList $first_sub $actual_type} all_comps]} {
        foreach c $all_comps {
            set cl [string tolower $c]
            if {$cl eq "x" || $cl eq "x-axis"} { set compX $c }
            if {$cl eq "y" || $cl eq "y-axis"} { set compY $c }
            if {$cl eq "z" || $cl eq "z-axis"} { set compZ $c }
        }
    }

    qry SetSelectionSet $sel_id
    qry SetQuery "element.id contour.value"

    set fp [open $filepath w]
    puts $fp "Loadcase_ID,Loadcase_Name,Element_ID,Ft,Force_X,RF_Tension,Fs,Force_Y,Force_Z,Shear_Force,RF_Shear"

    foreach sub $subcase_list {
        res SetCurrentSubcase $sub
        set sub_name [res GetSubcaseLabel $sub]
        set safe_sub_name [string map {"," "-"} $sub_name]

        # Use arrays to store the absolute extreme values per element ID
        array unset valX
        array unset valY
        array unset valZ

        if {$num_elems > 0} {
            foreach comp_name [list $compX $compY $compZ] arr_name [list valX valY valZ] {
                cont SetEnableState false
                cont SetDataType $actual_type
                
                if {![catch {cont SetDataComponent $comp_name}]} {
                    cont SetEnableState true
                    cli Draw
                    
                    qry GetIteratorHandle iter
                    for {iter First} {[iter Valid]} {iter Next} {
                        set lst [iter GetDataList]
                        set eid [lindex $lst 0]
                        set val [lindex $lst 1]
                        
                        if {[string is double -strict $val]} {
                            # Take Absolute Extreme if element has multiple values (e.g. End A, End B)
                            if {![info exists ${arr_name}($eid)]} {
                                set ${arr_name}($eid) $val
                            } else {
                                set exist_val [set ${arr_name}($eid)]
                                if {[expr {abs($val)}] > [expr {abs($exist_val)}]} {
                                    set ${arr_name}($eid) $val
                                }
                            }
                        }
                    }
                    iter ReleaseHandle
                }
            }
        }

        # Calculate Results and write row by row
        foreach eid [lsort -integer [array names valX]] {
            set fx $valX($eid)
            set fy [expr {[info exists valY($eid)] ? $valY($eid) : 0.0}]
            set fz [expr {[info exists valZ($eid)] ? $valZ($eid) : 0.0}]

            # Math formulas
            set rf_tension [SafeRF $Ft $fx]
            set shear [expr {sqrt( ($fy * $fy) + ($fz * $fz) )}]
            set rf_shear [SafeRF $Fs $shear]

            #set str_rf_tension [format "%.2f" $rf_tension]
            #set str_rf_shear [format "%.2f" $rf_shear]
            set str_fx [format "%.2f" $fx]
            set str_fy [format "%.2f" $fy]
            set str_fz [format "%.2f" $fz]
            set str_sh [format "%.2f" $shear]

            puts $fp "$sub,$safe_sub_name,$eid,$Ft,$str_fx,$rf_tension,$Fs,$str_fy,$str_fz,$str_sh,$rf_shear"
        }
    }

    close $fp

    tk_messageBox -message "Fastener Forces Export complete!\nSaved to: $filepath" -type ok -parent .exportUI

    mod RemoveSelectionSet $sel_id
    foreach h {cont res mod cli win page proj sess qry elem_set iter} { catch {$h ReleaseHandle} }
}
