Imports System.Collections


Public Class VBLinkedList(Of T)
    Implements VBCollection(Of T)

    Private first_element As VBLinkedListElement(Of T)
    Private last_element As VBLinkedListElement(Of T)
    Private element_count As Integer


    Public Sub Add(ByVal item As T) Implements System.Collections.Generic.ICollection(Of T).Add
        If first_element Is Nothing Then
            first_element = New VBLinkedListElement(Of T)(item)
            last_element = first_element
        Else
            last_element.setNext(item)
            last_element = last_element.getNext
        End If
        incCount()
    End Sub

    Public Sub AddFirst(ByVal item As T)
        If first_element Is Nothing Then
            first_element = New VBLinkedListElement(Of T)(item)
            last_element = first_element
        Else
            Dim old_first_element As VBLinkedListElement(Of T) = first_element
            first_element = New VBLinkedListElement(Of T)(item)
            first_element.setNext(old_first_element)
        End If
        incCount()
    End Sub

    Public Sub AddLast(ByVal item As T)
        Add(item)
    End Sub
    Public Sub RemoveFirst()
        If first_element IsNot Nothing Then
            first_element = first_element.getNext
            decCount()
        End If
    End Sub
    'Public Sub RemoveLast()
    '    If last_element Is Nothing Then
    'nothing
    '    Else
    'TODO! Shit ... how do we get around this nicely without making it a double linked list
    'last_element = last_element.getNext
    'decCount()
    '    End If
    'End Sub

    Public Sub Clear() Implements System.Collections.Generic.ICollection(Of T).Clear
        first_element = Nothing
        last_element = Nothing
        element_count = 0
    End Sub

    Public Function Contains(ByVal item As T) As Boolean Implements System.Collections.Generic.ICollection(Of T).Contains
        If item Is Nothing Then Return False
        Dim iterator As VBLinkedListIterator(Of T) = getVBIterator()
        Do While iterator.MoveNext
            If item.Equals(iterator.Current) Then Return True
        Loop
        Return False
    End Function

    Public Sub CopyTo(ByVal array() As T, ByVal arrayIndex As Integer) Implements System.Collections.Generic.ICollection(Of T).CopyTo
        'This is a guess, documentation is sketchy, I have not used arrayIndex so something is VERY wrong, investigate
        Dim iterator As VBLinkedListIterator(Of T) = getVBIterator()
        Dim counter As Integer = 0
        Do While iterator.MoveNext And counter < array.Length
            array(counter) = iterator.Current
            counter += 1
        Loop
    End Sub

    Public ReadOnly Property Count() As Integer Implements System.Collections.Generic.ICollection(Of T).Count
        Get
            Return element_count
        End Get
    End Property

    Public ReadOnly Property IsReadOnly() As Boolean Implements System.Collections.Generic.ICollection(Of T).IsReadOnly
        Get
            Return False
        End Get
    End Property

    Public Function Remove(ByVal item As T) As Boolean Implements System.Collections.Generic.ICollection(Of T).Remove
        If item Is Nothing Then Return False
        Dim remove_success As Boolean = False
        Dim iterator As VBLinkedListIterator(Of T) = getVBIterator()
        Do While iterator.MoveNext
            If item.Equals(iterator.Current) Then
                iterator.removeCurrent()
                remove_success = True
                Exit Do
            End If
        Loop
        If Count = 0 Then
            Clear()
        End If
        Return remove_success
    End Function

    Public Function GetEnumerator() As System.Collections.Generic.IEnumerator(Of T) Implements System.Collections.Generic.IEnumerable(Of T).GetEnumerator
        Return getVBIterator()
    End Function

    Public Function GetEnumerator1() As System.Collections.IEnumerator Implements System.Collections.IEnumerable.GetEnumerator
        Return getVBIterator()
    End Function

    Public Function getVBIterator() As VBIterator(Of T) Implements VBCollection(Of T).getVBIterator
        Return New VBLinkedListIterator(Of T)(Me)
    End Function


    '------------
    ' Friends for VBLinkedListElement management
    Friend Sub setFirst(ByRef new_first As VBLinkedListElement(Of T)) 'used iterator when first element removed
        first_element = new_first
    End Sub
    Friend Sub setLast(ByRef last As VBLinkedListElement(Of T)) 'used by iteratort to resync, final element, in case final element removed
        last_element = last
    End Sub
    Friend Function getFirst() As VBLinkedListElement(Of T)
        Return first_element
    End Function
    Friend Sub incCount() 'used by iterator addBefore and addAfter
        element_count += 1
    End Sub
    Friend Sub decCount() 'used by iterator remove
        element_count += -1
    End Sub


End Class







Public Class VBLinkedListIterator(Of T)
    Implements VBIterator(Of T)

    Private list As VBLinkedList(Of T)
    Private current_element As VBLinkedListElement(Of T)
    Private previous_element As VBLinkedListElement(Of T)

    Friend Sub New(ByRef list As VBLinkedList(Of T))
        Me.list = list
        Reset()
    End Sub

    Public Sub removeCurrent() Implements VBIterator(Of T).removeCurrent
        If previous_element Is Nothing Then
            list.setFirst(current_element.getNext)
        Else
            previous_element.setNext(current_element.getNext)
            current_element = previous_element 'so that MoveNext moved to the next element correctly
        End If
        list.decCount()
    End Sub

    Public Sub addAfter(ByRef item As T) Implements VBIterator(Of T).addAfter
        Dim next_element As VBLinkedListElement(Of T) = current_element.getNext
        Dim new_element As VBLinkedListElement(Of T) = New VBLinkedListElement(Of T)(item)
        current_element.setNext(new_element)
        new_element.setNext(next_element)
        list.incCount()
    End Sub

    Public Sub addBefore(ByRef item As T) Implements VBIterator(Of T).addBefore
        Dim new_element As VBLinkedListElement(Of T) = New VBLinkedListElement(Of T)(item)
        new_element.setNext(current_element)
        previous_element.setNext(new_element)
        list.incCount()
    End Sub

    Public ReadOnly Property Current() As T Implements System.Collections.Generic.IEnumerator(Of T).Current
        Get
            Return getCurrent()
        End Get
    End Property

    Public ReadOnly Property Current1() As Object Implements System.Collections.IEnumerator.Current
        Get
            Return getCurrent()
        End Get
    End Property

    Public Function MoveNext() As Boolean Implements System.Collections.IEnumerator.MoveNext
        previous_element = current_element
        If current_element Is Nothing Then
            current_element = list.getFirst()
        Else
            current_element = current_element.getNext()
        End If
        If current_element Is Nothing Then
            list.setLast(previous_element)
            Return False
        End If
        Return True
    End Function

    Public Sub Reset() Implements System.Collections.IEnumerator.Reset
        current_element = Nothing
        previous_element = Nothing
    End Sub

    Private Function getCurrent() As T
        If current_element Is Nothing Then Return Nothing
        Return current_element.VBLinkedListItem
    End Function

    Private disposedValue As Boolean = False        ' To detect redundant calls

    ' IDisposable
    Protected Overridable Sub Dispose(ByVal disposing As Boolean)
        If Not Me.disposedValue Then
            If disposing Then
                ' TODO: free other state (managed objects).
            End If

            ' TODO: free your own state (unmanaged objects).
            ' TODO: set large fields to null.
        End If
        Me.disposedValue = True
    End Sub

#Region " IDisposable Support "
    ' This code added by Visual Basic to correctly implement the disposable pattern.
    Public Sub Dispose() Implements IDisposable.Dispose
        ' Do not change this code.  Put cleanup code in Dispose(ByVal disposing As Boolean) above.
        Dispose(True)
        GC.SuppressFinalize(Me)
    End Sub
#End Region


End Class

Class VBLinkedListElement(Of T)

    Private element As T
    Private next_element_ref As VBLinkedListElement(Of T)

    Public Sub New(ByRef element As T)
        setThis(element)
    End Sub

    Public ReadOnly Property VBLinkedListItem() As T
        Get
            Return element
        End Get
    End Property

    Friend Sub setThis(ByRef element As T)
        Me.element = element
    End Sub
    Friend Sub setThis(ByRef element As VBLinkedListElement(Of T))
        setThis(element.VBLinkedListItem)
    End Sub

    Friend Sub setNext(ByRef next_element As T)
        If next_element Is Nothing Then
            next_element_ref = Nothing
        Else
            setNext(New VBLinkedListElement(Of T)(next_element))
        End If
    End Sub
    Friend Sub setNext(ByRef next_element As VBLinkedListElement(Of T))
        next_element_ref = next_element
    End Sub

    Friend Function hasNext() As Boolean
        If next_element_ref Is Nothing Then Return False
        Return True
    End Function
    Friend Function getNext() As VBLinkedListElement(Of T)
        Return next_element_ref
    End Function

    Public Overrides Function toString() As String
        Dim r As String = ""
        If element IsNot Nothing Then r += element.ToString
        If next_element_ref IsNot Nothing Then r += "," & next_element_ref.toString
        Return r
    End Function

End Class







Public Interface VBIterator(Of T)
    Inherits IEnumerator(Of T)
    Sub removeCurrent()
    Sub addBefore(ByRef item As T)
    Sub addAfter(ByRef item As T)
End Interface

Public Interface VBCollection(Of T)
    Inherits ICollection(Of T)
    Function getVBIterator() As VBIterator(Of T)
End Interface
