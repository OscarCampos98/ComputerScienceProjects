/**
 * StopWait protocol
 * 
 * CPSC 441
 * Assignment 4
 * 
 */

//import java.io.PrintWriter;
import java.util.*;
import java.util.logging.*;
//import javax.management.RuntimeErrorException;
import java.net.*;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.Paths;
//import java.io.BufferedReader;
//import java.io.DataOutputStream;
//import java.io.FilterOutputStream;
import java.io.*;
import java.util.logging.*;

public class StopWaitFtp {
	
	private static final Logger logger = Logger.getLogger("StopWaitFtp"); // global logger	

	/**
	 * Constructor to initialize the program 
	 * 
	 * @param timeout		The time-out interval for the retransmission timer, in milli-seconds
	 */

	 //time out constructor to be use later in the code when implementing the timer class.
	 int timeoutNeeded;

	public StopWaitFtp(int timeout){
		//like mention above the constructor for this protocol 
		//Variables needed for GzipClient
		 timeoutNeeded = timeout;
	}


	/**
	 * Send the specified file to the remote server
	 * 
	 * @param serverName	Name of the remote server
	 * @param serverPort	Port number of the remote server
	 * @param fileName		Name of the file to be trasferred to the rmeote server
	 */
	public void send(String serverName, int serverPort, String fileName){

		//variables needed to establish the handshake between the host and the server
		DataInputStream SockInstream;
		DataOutputStream SockoutStream;

		//timer class for this assignment
		//this class in incharge of any re transmition needed. Once the timer has been triggerd
		//the run method will take over and re transmit the package 
		//a message will be prop on the client side with the Timeout and Retransmitted sequence number
		class TimeoutHandler extends TimerTask{			
			
			//variables needed for our Timer class
			DatagramSocket clientSocketNeeded;

			//a segment copy will be provided to avoid any race conditions
			FtpSegment segment_copy;
			DatagramPacket packet_R;
			int seqNum_R;

			//Our class Constructor
			public TimeoutHandler(DatagramSocket clientSocket, FtpSegment segment_S, DatagramPacket packet, int seqNum) {
				clientSocketNeeded = clientSocket;
				segment_copy = segment_S;
				packet_R = packet;
				seqNum_R = seqNum;
			}
			public void run(){
				//time out indication by the thread to be print on the screen 
				System.out.println("TimeOut");
			
				//when the timer has expired and no ack has been received 
				//retransmit the current segment.
				try {
					//retransmition of the packet 
					clientSocketNeeded.send(packet_R);
					System.out.println("retx:  " + "<"+seqNum_R+">");
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		
		}

		//establishing the handshake proccess for our assingment. like mention we need a TCP and UDP socket 

		 //stablish a TCP connectiong with the server 
		 //exchnage information about filename, its length,the initial seq#, and UDP port on sender and reciever
		 InetSocketAddress serverAddress = new InetSocketAddress(serverName,serverPort);
		 // System.out.println(serverAddress);
		 
		 //Creating a new TCP socket
		 Socket socket = new Socket(); 
		 
		//length of a file (in bytes) as a long val. we will use path and file to accomplish this
		Path path = Paths.get(fileName);

		 try {
			 //TCP and Stream connection with the server  
			 socket.connect(serverAddress);
			 SockInstream = new DataInputStream(socket.getInputStream());
			 SockoutStream = new DataOutputStream(socket.getOutputStream());

			 //UDP and Streams connection with the server 
			 DatagramSocket clientSocket = new DatagramSocket();
			 int UDPport = clientSocket.getLocalPort();
			 
			 //hostname to IP
			 InetAddress IPAddress = InetAddress.getByName(serverName);
			
			 //getting the size of the inputfile as a Long using File path
			 long bytesNeeded = Files.size(path);
			
			 //lets provide the server with the handshake and flush after each data send
			 SockoutStream.writeInt(UDPport);
			 SockoutStream.flush();
			 SockoutStream.writeUTF(fileName);
			 SockoutStream.flush();
			 SockoutStream.writeLong(bytesNeeded);
			 SockoutStream.flush();


			 //now we wait for the server to send us data we need for the UDP socket
			 int Rservep = SockInstream.readInt();
			 int SeqNum = SockInstream.readInt();  

			 //close stream to avoid any leak information
			 SockInstream.close();
			 SockoutStream.close();

			
			 //Now that we have the information require for the data transfer we will implement the 
			 //Stop and wait protocol 

			 //We open the file given to us by the client to be read and transmitted
			 FileInputStream in = null;
			 in = new FileInputStream(fileName);

			 //the recomended size of each segment by the Ftp segment
			 byte[] buff_write = new byte [1000];
			 int c;

			 // creation of the timer object to be use for retransmition	
			 Timer timer = new Timer();
			 
			 //while the file is not empty we will read from it in chucks and incapsulate them to be transfer
			 while((c = in.read(buff_write)) != -1){

				//read fromm the file and create segments 
				FtpSegment segment_S = new FtpSegment(SeqNum, buff_write, 1000 );
				
				//pack and send the segments to the server through a Datagram
				DatagramPacket packet = FtpSegment.makePacket(segment_S, IPAddress, Rservep);
				clientSocket.send(packet);
				
				//print statements require by the program
				System.out.println("Send:  " + "<"+SeqNum+">");
				
				//creation of the timer thread and a schedule of a fixed rate
				TimerTask NewTask = new TimeoutHandler(clientSocket, segment_S, packet, SeqNum);
				timer.scheduleAtFixedRate(NewTask,timeoutNeeded, timeoutNeeded);


				//read the datagram from the server and decap it.
				clientSocket.receive(packet);
				FtpSegment segment_R = new FtpSegment(packet);

				//wait for ACK, when correct ACK arrives stop the timer
				//expected ACK = ACK + 1

				//get the sequence number from the server 
				int num_recived = segment_R.getSeqNum();

				//check is what we expect from the server 
				int check = SeqNum +1;

				//if we recive the correct ACK from the server by checking the ack recived and the one we expect
				if (num_recived == check){
					//print statment require by the problem and in this case is the package recieved
					System.out.println("ACK: " + "<" +num_recived+ ">");
					//since we recived the correct ACK there is no need for any retransmitions 
					//cancel the timer task for this segment 
					NewTask.cancel();
					//increment the sequence number in order to send the next pack	
					SeqNum++;
				}

			 }

			 //close the sockets, timer, and any open streams
			 timer.cancel();
			 timer.purge();
			 in.close();
			 clientSocket.close(); 

			
			}catch(ConnectException e){
				System.out.println("You Have Enter the Wrong Port#\n or the wrong Servername");
				System.exit(0);	
			}catch(NoSuchFileException e){
				System.out.println("The File You Wish To Send Does Not Exist\n Try New File Name");
				System.exit(0);	
			}
			catch(IOException e){
				e.printStackTrace();
				System.exit(0);

			}
			
		//close the program 
		System.exit(0);	
	}

} // end of class