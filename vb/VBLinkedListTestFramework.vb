Module Module1

    Class TestClass
        Public Sub New(ByVal item As String)
            Me.item = item
        End Sub
        Public item As String
        Public Overrides Function toString() As String
            Return item
        End Function
    End Class

    Sub Main()
        Dim list = New VBLinkedList(Of TestClass)
        list.Add(New TestClass("A"))
        list.Add(New TestClass("B"))
        list.Add(New TestClass("C"))
        list.Add(New TestClass("D"))
        list.RemoveFirst()
        list.AddFirst(New TestClass("E"))
        list.AddFirst(New TestClass("F"))

        Console.WriteLine("F,E,B,C,D,")
        For Each item In list
            Console.Write(item.item & ",")
        Next
        Console.WriteLine()

        ' Modify the list with the new style of iterator
        Dim iterator As VBLinkedListIterator(Of TestClass) = list.getVBIterator
        Do While iterator.MoveNext
            If (iterator.Current.item = "C") Then  'New TestClass("C")
                iterator.addBefore(New TestClass("G"))
            End If
            If (iterator.Current.item = "E") Then
                iterator.addAfter(New TestClass("H"))
            End If
            If (iterator.Current.item = "B") Then
                iterator.removeCurrent()
            End If
        Loop

        Console.WriteLine("F,E,H,G,C,D,")
        For Each item In list
            Console.Write(item.item & ",")
        Next
        Console.WriteLine()

        list.Clear()
        list.AddLast(New TestClass("I"))
        list.RemoveFirst()
        list.AddLast(New TestClass("J"))
        iterator = list.getVBIterator
        Do While iterator.MoveNext
            If (iterator.Current.item = "J") Then
                iterator.addAfter(New TestClass("K"))
                iterator.removeCurrent()
            End If
            If (iterator.Current.item = "K") Then
                iterator.addAfter(New TestClass("L"))
            End If
        Loop

        Console.WriteLine("K,L,")
        For Each item In list
            Console.Write(item.item & ",")
        Next
        Console.WriteLine()

        Console.ReadLine()
    End Sub

End Module
